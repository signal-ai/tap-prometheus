from datetime import datetime
import os
import json
import uuid
import hashlib

import singer
from singer import utils

from promalyze import Client

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    'queries', 'prometheus_endpoint', 'start_date', 'stream_name'
]

def construct_schema(queries_results):
    all_labels = set()
    for (query_id, result) in queries_results.items():
        for vector in result.vectors:
            all_labels.update(vector.metadata.keys())

    prefixed_labels = [f"labels__{label}" for label in all_labels]
    schema = {'properties': {'id': {'type': 'string'},
                             'query_id': {'type': 'string'},
                             'labels_hash': {'type': 'string'},
                             'value': {'type': 'string'},
                             'timestamp': {'type': 'long'}}}

    for label in prefixed_labels:
        schema["properties"][label] = {'type': 'string'}

    return schema

def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()

def calc_labels_hash(labels):
    return sha1(json.dumps(sorted(labels.items())))

def output_results(stream_name, queries_results, extraction_time=singer.utils.now()):
    for (query_id, results) in queries_results.items():
        for vector in results.vectors:
            labels_hash = calc_labels_hash(vector.metadata)

            record = {'id': sha1(f"{query_id}|{labels_hash}|{vector.timestamp}"),
                      'query_id': query_id,
                      'labels_hash': labels_hash,
                      'value': vector.value,
                      'timestamp': vector.timestamp}
            for (label_name, label_value) in vector.metadata.items():
                record[f"labels__{label_name}"] = label_value

            singer.write_record(stream_name,
                                record,
                                time_extracted=extraction_time)


def query(args):
    queries = args.config['queries']
    client = Client(args.config['prometheus_endpoint'])
    start_date = args.config['start_date']
    stream_name = args.config['stream_name']

    queries_results = {}
    extraction_time = singer.utils.now()

    for (query_id, query) in queries.items():
        queries_results[query_id] = client.instant_query(
            query,
            params={"time": start_date}
        )

    schema = construct_schema(queries_results)

    singer.write_schema(stream_name, schema, ['id'])

    output_results(stream_name, queries_results, extraction_time)

def main():
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    if args.discover:
        # Catalog is not supported, output a minimal object to allow parsing
        print(json.dumps({"streams" : []}))
    else:
        query(args)

if __name__ == '__main__':
    main()
