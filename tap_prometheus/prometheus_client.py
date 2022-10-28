from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests
import singer
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

LOGGER = singer.get_logger()


def _default_retry_client():
    return Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504],
    )


@dataclass
class PrometheusResult:
    labels: Dict[str, str]
    values: List[Tuple[float, str]]


class PrometheusClient:
    """
    A Prometheus API client for making Prometheus queries

    :param url: (str) url for the prometheus host
    :param headers: (dict) A dictionary of http headers to be used to communicate with
        the host. Example: {"Authorization": "bearer my_oauth_token_to_the_host"}
    :param enable_ssl: (bool) If set to False, will disable ssl certificate verification
        for the http requests made to the prometheus host
    :param retry: (Retry) A urllib Retry adapter to configure the HTTP client retries
    """

    def __init__(
        self,
        url: str = "http://127.0.0.1:9090",
        headers: dict = None,
        enable_ssl: bool = True,
        retry: Retry = None,
    ):
        if url is None:
            raise TypeError("The parameter url is undefined")

        self.headers = headers
        self.url = url
        self.prometheus_host = urlparse(self.url).netloc
        self.ssl_verification = enable_ssl

        if retry is None:
            retry = _default_retry_client()

        self._session = requests.Session()
        self._session.mount(self.url, HTTPAdapter(max_retries=retry))

    def _parse_query_result(self, result) -> List[PrometheusResult]:
        results = []
        for item in result:
            values = item.get("values")
            if not values:
                values = [item.get("value")]
            values = [[value[0], value[1]] for value in values]
            results.append(PrometheusResult(labels=item["metric"], values=values))
        return results

    def query(self, query: str, params: dict = None):
        """
        Send a query to Prometheus.

        :param query: (str) A PromQL query, see https://prometheus.io/docs/prometheus/latest/querying/examples/ for examples
        :param params: (dict) Optional dictionary containing GET parameters to be
            sent along with the API request, such as "time"
        :returns: (list) A list of metric data received in response of the query sent
        :raises:
            (RequestException) In the event of a connection error
            (PrometheusApiClientException) In the event of a non-200 response status code from the Prometheus API
        """
        params = params or {}
        query = str(query)
        response = self._session.get(
            f"{self.url}/api/v1/query",
            params={**{"query": query}, **params},
            verify=self.ssl_verification,
            headers=self.headers,
        )
        if response.status_code == 200:
            result = response.json()["data"]["result"]

            return self._parse_query_result(result)
        else:
            raise PrometheusApiException(
                f"HTTP Status Code {response.status_code} ({response.content!r})"
            )


class PrometheusApiException(Exception):
    """API exception, raises when response status code != 200."""

    pass
