import datetime

import tap_prometheus as tap
from pytest_httpserver import HTTPServer


def test_query(httpserver: HTTPServer):
    httpserver.expect_request("/api/v1/query").respond_with_json(
        {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "up",
                            "job": "prometheus",
                            "instance": "localhost:9090",
                        },
                        "values": [
                            [1435781430.781, "1"],
                        ],
                    },
                    {
                        "metric": {
                            "__name__": "up",
                            "job": "node",
                            "instance": "localhost:9091",
                        },
                        "values": [
                            [1435781430.781, "0"],
                        ],
                    },
                ],
            },
        }
    )

    url = httpserver.url_for("")

    config = {
        "queries": {"query_1": "123"},
        "prometheus_endpoint": url,
        "start_date": "2022-01-01T00:00:00Z",
        "stream_name": "prometheus",
    }
    tap_config = tap.parse_tap_config(config)
    result = tap.query(tap_config)

    assert result["records"] == {
        "query_1": [
            {
                "id": "d056117cba16f8b10eca3f00d80f19c25a24c8d8",
                "labels__instance": "localhost:9090",
                "labels__job": "prometheus",
                "labels_hash": "a7520dca2ca10ef6bc0db4c018d8eafe78fb7a74",
                "query_id": "query_1",
                "timestamp": datetime.datetime(2015, 7, 1, 20, 10, 30, 780999),
                "value": 1,
            },
            {
                "id": "5da0e61681c1c3acebdcf8609fb4edfdb7c4a33f",
                "labels__instance": "localhost:9091",
                "labels__job": "node",
                "labels_hash": "eadb16ede95a4076e4396c4ee8d3e2346febf9dc",
                "query_id": "query_1",
                "timestamp": datetime.datetime(2015, 7, 1, 20, 10, 30, 780999),
                "value": 0,
            },
        ]
    }


def test_query_with_no_name_in_result(httpserver: HTTPServer):
    httpserver.expect_request("/api/v1/query").respond_with_json(
        {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "job": "prometheus",
                            "instance": "localhost:9090",
                        },
                        "values": [
                            [1435781430.781, "1"],
                        ],
                    },
                    {
                        "metric": {
                            "job": "node",
                            "instance": "localhost:9091",
                        },
                        "values": [
                            [1435781430.781, "0"],
                        ],
                    },
                ],
            },
        }
    )

    url = httpserver.url_for("")

    config = {
        "queries": {"query_1": "123"},
        "prometheus_endpoint": url,
        "start_date": "2022-01-01T00:00:00Z",
        "stream_name": "prometheus",
    }
    tap_config = tap.parse_tap_config(config)
    result = tap.query(tap_config)

    assert result["records"] == {
        "query_1": [
            {
                "id": "d056117cba16f8b10eca3f00d80f19c25a24c8d8",
                "labels__instance": "localhost:9090",
                "labels__job": "prometheus",
                "labels_hash": "a7520dca2ca10ef6bc0db4c018d8eafe78fb7a74",
                "query_id": "query_1",
                "timestamp": datetime.datetime(2015, 7, 1, 20, 10, 30, 780999),
                "value": 1,
            },
            {
                "id": "5da0e61681c1c3acebdcf8609fb4edfdb7c4a33f",
                "labels__instance": "localhost:9091",
                "labels__job": "node",
                "labels_hash": "eadb16ede95a4076e4396c4ee8d3e2346febf9dc",
                "query_id": "query_1",
                "timestamp": datetime.datetime(2015, 7, 1, 20, 10, 30, 780999),
                "value": 0,
            },
        ]
    }
