from datetime import datetime
import os
import json

import singer
from singer import utils, Transformer
from singer import metadata

from promalyze import Client

client = Client("http://prometheus-a.signal")

LOGGER = singer.get_logger()

def main_range():
    #args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    query = "slo:sli_error:ratio_rate1d"

    start_time = 1655123817 # yesterday
    day = 86400 #day
    step = day

    end_time =  start_time + day # today

    ts_data = client.range_query(
        query,
        start=start_time,
        end=end_time,
        step=step
    )

    print(ts_data.timeseries[0].as_json())


# {'query_id': 'sli_error_rate',
#  'value': "0.0001234",
#  'timestamp': 1655123817,
#  'labels__sloth_slo': "worker_prod_sentence_sentiment_prediction_v2_latency_99_percent_documents_processed_within_6_seconds"
#  }
def get_prometheus_data():
    query = "slo:sli_error:ratio_rate1d"

    start_time = 1655123817 # yesterday
    day = 86400 #day
    step = day

    end_time =  start_time + day # today

    ts_data = client.instant_query(
        query,
        params={"time": start_time}
    )

    print(ts_data.as_json())
    print(ts_data.vectors[0].value)

    return ts_data

def main():
    #args = utils.parse_args(REQUIRED_CONFIG_KEYS)


    # config: {query_id: query}
    {'sli_error_rate': "slo:sli_error:ratio_rate1d"}
    stream_name = "prometheus_query_results"
    schema = {'properties': {'id': {'type': 'string'},
                             'query_id': {'type': 'string'},
                             'value': {'type': 'string'},
                             'timestamp': {'type': 'long'},
                             'labels__sloth_slo': {'type': 'string'}
                             }}

    singer.write_schema(stream_name, schema, ['id'])

    test_record =  {'id': "blabla",
                    'query_id': 'sli_error_rate',
                    'value': "0.0001234",
                    'timestamp': 1655123817,
                    'labels__sloth_slo': "worker_prod_sentence_sentiment_prediction_v2_latency_99_percent_documents_processed_within_6_seconds"
                    }
    extraction_time = singer.utils.now()
    singer.write_record(stream_name,
                        test_record,
                        time_extracted=extraction_time
                    )
    singer.write_record(stream_name,
                        test_record,
                        time_extracted=extraction_time
                    )



if __name__ == '__main__':
    main()
