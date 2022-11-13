from dataclasses import dataclass
from decimal import Decimal
from typing_extensions import Self
import boto3
from boto3.dynamodb.conditions import Key
import uuid
from enum import Enum
from meta_data import ServiceType

TABLE_SERVICES = "dra-services-prod"



@dataclass
class ServiceRevenueDeclaration:
    
    
    type:ServiceType
    business:str
    label:str
    client:str
    month:int
    year:int
    amount:Decimal
    currency:str
    uuid:str = "N/A"
    period:str = "N/A"


    def Save(self):
        id = str(self.year)+'-'+str(self.month)
        dynamodb = boto3.client('dynamodb')
        dynamodb.put_item(TableName=TABLE_SERVICES, Item={
        'period':{'S':id},
        'uuid':{'S': self.client+'#'+str(uuid.uuid4())},
        'type':{'S':self.type},
        'business':{'S':self.business},
        'label':{'S':self.label},
        'client':{'S':self.client},
        'month':{'N':str(self.month)},
        'year':{'N':str(self.year)},
        'amount':{'S':str(self.amount)},
        'currency':{'S':self.currency}
        })

    @staticmethod
    def DeleteByUUID(period,uuid):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(TABLE_SERVICES)
        resp = table.delete_item(
        Key={
            'period':period,
            'uuid': uuid
        })
        return resp


    @staticmethod
    def List(month,year):
        srd_list = []
        dynamodb = boto3.resource('dynamodb')
        transaction_table = dynamodb.Table(TABLE_SERVICES)
        id = str(year)+'-'+str(month)
        response = transaction_table.query(
        KeyConditionExpression = Key("period").eq(id) 
        )

        ddb_srds = response['Items']

        for ddb_srd in ddb_srds:
            
            srd = ServiceRevenueDeclaration(
                
                ddb_srd["type"],
                ddb_srd['business'],
                ddb_srd['label'],
                ddb_srd['client'],
                int(ddb_srd['month']),
                int(ddb_srd['year']),
                Decimal(ddb_srd['amount']),
                ddb_srd['currency'],
                ddb_srd["uuid"],
                ddb_srd['period']
            )

           

            srd_list.append(srd)

        return srd_list

    @staticmethod
    def ListForClient(month,year,client):
        srd_list = []
        dynamodb = boto3.resource('dynamodb')
        transaction_table = dynamodb.Table(TABLE_SERVICES)
        id = str(year)+'-'+str(month)
        response = transaction_table.query(
        KeyConditionExpression = Key("period").eq(id) & Key("uuid").begins_with(client)
        )

        ddb_srds = response['Items']

        for ddb_srd in ddb_srds:
            
            srd = ServiceRevenueDeclaration(
                ddb_srd["type"],
                ddb_srd["business"],
                ddb_srd['label'],
                ddb_srd['client'],
                int(ddb_srd['month']),
                int(ddb_srd['year']),
                Decimal(ddb_srd['amount']),
                ddb_srd['currency'],
                ddb_srd["uuid"],
                ddb_srd['period']
            )

           
            if srd.client==client:
                srd_list.append(srd)

        return srd_list


