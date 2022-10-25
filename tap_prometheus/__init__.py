import hashlib
import json
from dataclasses import dataclass

import singer
from pandas import DataFrame, Timestamp
from prometheus_api_client import Metric, MetricsList, PrometheusConnect
from singer import utils

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = ["queries", "prometheus_endpoint", "start_date", "stream_name"]


def construct_schema(records):
    all_labels = set()
    for record in records:
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


def calc_labels_hash(labels):
    return sha1(json.dumps(sorted(labels.items())))


def parse_metrics(query_id, metrics: MetricsList):
    records = []
    for metric in metrics:
        metric: Metric
        metric_values: DataFrame = metric.metric_values

        labels_hash = calc_labels_hash(metric.label_config)
        label_cols = {}
        for (label_name, label_value) in metric.label_config.items():
            label_cols[f"labels__{label_name}"] = label_value

        for index, row in metric_values.iterrows():
            dt: Timestamp = row["ds"]
            value = row["y"]

            records.append(
                {
                    **label_cols,
                    **{
                        "id": sha1(f"{query_id}|{labels_hash}|{dt}"),
                        "timestamp": dt.to_pydatetime(),
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
    client: PrometheusConnect
    start_date: str
    stream_name: str


def parse_tap_config(config):
    disable_ssl = config.get("disable_ssl", True)
    return TapConfig(
        queries=config["queries"],
        client=PrometheusConnect(
            url=config["prometheus_endpoint"], disable_ssl=disable_ssl
        ),
        start_date=config["start_date"],
        stream_name=config["stream_name"],
    )


def query(config: TapConfig):
    records = {}
    extraction_time = utils.now()

    for (query_id, query) in config.queries.items():
        query_result = config.client.custom_query(
            query, params={"time": config.start_date}
        )
        records[query_id] = parse_metrics(query_id, MetricsList(query_result))

    return {"extraction_time": extraction_time, "records": records}


def write_query_results_in_singer_format(extraction_time, result, config: TapConfig):
    extraction_time = result["extraction_time"]
    records = result["records"]

    schema = construct_schema(records)
    singer.write_schema(config.stream_name, schema, ["id"])

    for records in records.values():
        for record in records:
            singer.write_record(
                config.stream_name, record, time_extracted=extraction_time
            )


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
