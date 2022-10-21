# import sys
# sys.path.append(r'/home/jrecan/dra-pipelines/pipelines')
# print('\n'.join(sys.path))


import json
import logging
import time
import traceback
import requests
import boto3
from marketplace_model import MarketPlaceReport
from marketplace_controller import BuildMarketplaceReport
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import utils

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        LOGGER.info('Started Marketplace Lambda')

        report = BuildMarketplaceReport(event['month'],event['year'])

        print(json.dumps(report.to_dict(), sort_keys=True, indent=4, cls=utils.JSONEncoder))

        return {
        'statusCode': 200,
        'body': "{}".format(
            report.to_json()
        )
    }
    except Exception as e:
        traceback.print_exc()

        response_data = {
            'statusCode': 500,
            'error': str(e)
        }
    return response_data

if __name__ == "__main__":
    x = lambda_handler(0,0)
    print(x)


