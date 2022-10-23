
import json
import logging
import time
import traceback
import requests
import boto3
from product_marketplace_model import MarketplaceReport, MarketplaceTransaction
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TABLE_TRANSACTIONS = "reportingTransactions"

def BuildMarketplaceReport(month, year):

    report = MarketplaceReport(month,year)

    id_key = str(year)+"-"
    if month < 10:
        id_key =id_key +"0"+ str(month)
    else:
        id_key += str(month)

    
    dynamodb = boto3.resource('dynamodb')
    transaction_table = dynamodb.Table(TABLE_TRANSACTIONS)

    response = transaction_table.query(
        KeyConditionExpression = Key("Id").eq(id_key)
    )

    transactions = response['Items']


    nb_transactions = 0

    if (len(transactions)>0):
        # print(transactions[0])
        for transaction in transactions:

            tr = MarketplaceTransaction(
                transaction['SupplierName'],
                transaction['ClientCode'],
                transaction['ClientCurrencyCode'],
                transaction['SupplierCurrencyCode'],
                transaction['ClientTransactionAmount'],
                transaction['SupplierTransactionAmount'],
                transaction['CalculatedMargin'],
                str(month)+"/"+str(year)
            )
            report.addTransaction(tr)

        report.Save()



        print(report.margins_frame.to_json())

        return report    
    else:
        print("no transactions available") 
        return {} 