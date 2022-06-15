from datetime import datetime
import os
import json
import uuid

import singer
from singer import utils

from promalyze import Client

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    'queries', 'prometheus_endpoint'
]

STREAM_NAME = "prometheus_query_results"

def construct_schema(queries_results):
    all_labels = set()
    for (query_id, result) in queries_results.items():
        for vector in result.vectors:
            all_labels.update(vector.metadata.keys())

    prefixed_labels = [f"labels__{label}" for label in all_labels]
    schema = {'properties': {'id': {'type': 'string'},
                             'query_id': {'type': 'string'},
                             'value': {'type': 'string'},
                             'timestamp': {'type': 'long'}}}

    for label in prefixed_labels:
        schema["properties"][label] = {'type': 'string'}

    return schema

def output_results(queries_results, extraction_time=singer.utils.now()):
    for (query_id, results) in queries_results.items():
        for vector in results.vectors:
            record = {'id': str(uuid.uuid4()),
                      'query_id': query_id,
                      'value': vector.value,
                      'timestamp': vector.timestamp}
            for (label_name, label_value) in vector.metadata.items():
                record[f"label__{label_name}"] = label_value

            singer.write_record(STREAM_NAME,
                                record,
                                time_extracted=extraction_time)

def main():
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    queries = args.config['queries']
    client = Client(args.config['prometheus_endpoint'])

    queries_results = {}
    extraction_time = singer.utils.now()

    for (query_id, query) in queries.items():
        if(query["type"]=="instant"):
            queries_results[query_id] = client.instant_query(
                query["query"],
                params={"time": query["params"]["time"]}
            )
        else:
            raise Exception(f"Unsupported query type: {query['type']}. Only 'instant' queries are supported.")

    schema = construct_schema(queries_results)

    singer.write_schema(STREAM_NAME, schema, ['id'])

    output_results(queries_results, extraction_time)


if __name__ == '__main__':
    main()
