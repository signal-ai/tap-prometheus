# tap-prometheus

[Singer](https://www.singer.io/) tap that extracts data from [Prometheus](https://prometheus.io/) using queries provided in config and produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md).

## Building and running locally

The project uses `pyenv` and `poetry` to manage its dependencies.

To install the tools required you can run `make install-tools`.

To install the dependencies, run `make install-dependencies`.

To start the project, run `make start`. This uses an example config in `example_config.json`.

## Configuration and functionality
Configuration is as follows:
```json
{
    "stream_name": "prometheus",
    "prometheus_endpoint": "http://prometheus-a.mydomain",
    "start_date": "2022-06-16T00:00:00Z",
    "queries":{"my_query_id":"my_promql_query"}
}
```
With this configuration, it will run instance queries from `queries` field (one request for each query) for the given `start_date` on the given prometheus endpoint.

The intended use case for this tap is getting started by Airflow on schedule and it's output being saved in a Data warehouse.
This tap does not support state, or discovery: running it with `-d` option is a no-op, this also means that catalog is not ignored.

The tap outputs records with the following fields: 
 - `id`: hash of every field except value for deduplication, primary key,
 - `query_id`: taken from the input config,
 - `labels_hash`: hash of the values of all `label__{label_name}` fields,
 - `value`: metric value,
 - `timestamp`: timestamp of the metric
 - `label__{label_name}`: each metric label and it's value is outputted like this (flattened)

Every query can output many records with different labels.
Schema is computed automatically with all the labels in the result set (one schema per run).
