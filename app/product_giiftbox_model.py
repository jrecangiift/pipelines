from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import boto3

@dataclass
@dataclass_json
class GiiftBoxMonthlyReport:
    Merchant_Total_Count: int =0
    Merchant_ThisMonth_Added:int = 0
    offer_Total__Count: int =0 
    offer_ThisMonth_Added: int = 0

    GIIFTBOX_DATA_BUCKET = 'dra-box-prod'

    @staticmethod
    def Load(client_code, month, year):
        s3_client = boto3.client('s3')
        key = client_code+"@"+str(month)+"@"+str(year)+".json"
        data = s3_client.get_object(Bucket=GiiftBoxMonthlyReport.GIIFTBOX_DATA_BUCKET, Key=key)
        contents = data['Body'].read()
        report = GiiftBoxMonthlyReport.from_json(contents)
        return report