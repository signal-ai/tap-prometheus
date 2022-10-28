import datetime
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List

import singer
from dateutil import parser
from singer import utils

from tap_prometheus.prometheus_client import PrometheusClient, PrometheusResult

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = ["queries", "prometheus_endpoint", "start_date", "stream_name"]


def construct_schema(records: Dict[str, List[Dict[str, Any]]]):
    all_labels = set()
    for named_record in records.values():
        for record in named_record:
            for key in record.keys():
                if key.startswith("labels__"):
                    all_labels.add(key)

    schema = {
        "properties": {
            "id": {"type": "string"},
            "query_id": {"type": "string"},
            "labels_hash": {"type": "string"},
            "value": {"type": "string"},
            "timestamp": {"type": "long"},
        }
    }

    for label in all_labels:
        schema["properties"][label] = {"type": "string"}

    return schema


def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def calc_labels_hash(labels: Dict):
    return sha1(json.dumps(sorted(labels.items())))


def parse_metrics(query_id, query_result: List[PrometheusResult]):
    records = []

    for result in query_result:
        labels_hash = calc_labels_hash(result.labels)
        label_cols = {}
        for (label_name, label_value) in result.labels.items():
            if label_name == "__name__":
                label_cols["labels__name"] = label_value
            else:
                label_cols[f"labels__{label_name}"] = label_value

        for value in result.values:
            dt_epoch = value[0]
            value = value[1]

            records.append(
                {
                    **label_cols,
                    **{
                        "id": sha1(f"{query_id}|{labels_hash}|{dt_epoch}"),
                        "timestamp": datetime.datetime.fromtimestamp(
                            dt_epoch, tz=datetime.timezone.utc
                        ).isoformat(),
                        "query_id": query_id,
                        "labels_hash": labels_hash,
                        "value": value,
                    },
                }
            )
    return records


@dataclass
class TapConfig:
    queries: map
    client: PrometheusClient
    start_date: str
    stream_name: str


def parse_tap_config(config):
    enable_ssl = config.get("enable_ssl", config["prometheus_endpoint"].startswith("https"))
    parsed_time = parser.parse(config["start_date"])
    return TapConfig(
        queries=config["queries"],
        client=PrometheusClient(url=config["prometheus_endpoint"], enable_ssl=enable_ssl),
        start_date=parsed_time.isoformat(),
        stream_name=config["stream_name"],
    )


def query(config: TapConfig):
    records = {}
    extraction_time = utils.now()

    for (query_id, query) in config.queries.items():
        query_result = config.client.query(query, params={"time": config.start_date})
        records[query_id] = parse_metrics(query_id, query_result)

    return {"extraction_time": extraction_time, "records": records}


def write_query_results_in_singer_format(result, config: TapConfig):
    extraction_time = result["extraction_time"]
    records = result["records"]

    schema = construct_schema(records)
    singer.write_schema(config.stream_name, schema, ["id"])

    for records in records.values():
        for record in records:
            LOGGER.debug("Record %s", record)
            singer.write_record(config.stream_name, record, time_extracted=extraction_time)


def main():
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    if args.discover:
        # Catalog is not supported, output a minimal object to allow parsing
        print(json.dumps({"streams": []}))
    else:
        tap_config = parse_tap_config(args.config)
        results = query(tap_config)
        write_query_results_in_singer_format(results, tap_config)


if __name__ == "__main__":
    main()
