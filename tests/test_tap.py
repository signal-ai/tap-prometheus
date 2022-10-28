import datetime

from pytest_httpserver import HTTPServer

import tap_prometheus as tap


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
                "id": "9455c3fe84216e53d89a8643797fb399549461b8",
                "labels__instance": "localhost:9090",
                "labels__job": "prometheus",
                "labels__name": "up",
                "labels_hash": "385c9ae2c7b19b739a5728b38adf5297c6c03e89",
                "query_id": "query_1",
                "timestamp": datetime.datetime(
                    2015, 7, 1, 20, 10, 30, 781000, tzinfo=datetime.timezone.utc
                ),
                "value": 1,
            },
            {
                "id": "7ec787490fc5052611881cf826fa51cf16a49b51",
                "labels__instance": "localhost:9091",
                "labels__job": "node",
                "labels__name": "up",
                "labels_hash": "d18aea204e3cdd36cd0bcf1ae8f5c1811cd54fb2",
                "query_id": "query_1",
                "timestamp": datetime.datetime(
                    2015, 7, 1, 20, 10, 30, 781000, tzinfo=datetime.timezone.utc
                ),
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
                "id": "d8af591e3b46ac1d463c24762216f6dd43bcd18b",
                "labels__instance": "localhost:9090",
                "labels__job": "prometheus",
                "labels_hash": "a7520dca2ca10ef6bc0db4c018d8eafe78fb7a74",
                "query_id": "query_1",
                "timestamp": datetime.datetime(
                    2015, 7, 1, 20, 10, 30, 781000, tzinfo=datetime.timezone.utc
                ),
                "value": 1,
            },
            {
                "id": "190710b2ac1e16c9d093ade016b7bc814e54bb11",
                "labels__instance": "localhost:9091",
                "labels__job": "node",
                "labels_hash": "eadb16ede95a4076e4396c4ee8d3e2346febf9dc",
                "query_id": "query_1",
                "timestamp": datetime.datetime(
                    2015, 7, 1, 20, 10, 30, 781000, tzinfo=datetime.timezone.utc
                ),
                "value": 0,
            },
        ]
    }
