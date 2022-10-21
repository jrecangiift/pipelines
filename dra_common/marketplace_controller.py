
import json
import logging
import time
import traceback
import requests
import boto3
from marketplace_model import MarketPlaceReport
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TABLE_TRANSACTIONS = "reportingTransactions"

def BuildMarketplaceReport(month, year):

    report = MarketPlaceReport(month,year)

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

            supplier_name = transaction['SupplierName']
            supplier_currency = transaction['SupplierCurrencyCode']
            supplier_amount = transaction['SupplierTransactionAmount']
            margin = transaction['CalculatedMargin']

            client_currency = transaction['ClientCurrencyCode']
            client_amount = transaction['ClientTransactionAmount']
            client_code = transaction['ClientCode']



            # Build the supplier name into currency dictionary
            report.addSupplierTransaction(supplier_name,supplier_currency,margin,supplier_amount)
            report.addClientTransaction(supplier_name,supplier_currency,margin,supplier_amount)

            # # Market & Credit Risk Register
            # if (client_amount) != supplier_amount:
            #     print(client_code+": "+str(client_amount-supplier_amount))
            #     # print(json.dumps(transaction, sort_keys=True, indent=4, cls=JSONEncoder))
            
        return report    
    else:
        print("no transactions available") 
        return {} 