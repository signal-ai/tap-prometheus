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
    "prometheus_endpoint": "http://prometheus-a.mydomain",
    "start_date": "2022-06-16T00:00:00Z",
    "queries":{"my_query_id":"my_promql_query"}
}
```
With this configuration, it will run instance queries from `queries` field (one request for each query) for the given `start_date` on the given prometheus endpoint.
This tap does not support state.
