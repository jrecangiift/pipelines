
import json
import logging
import time
import traceback
import requests
import boto3
from product_marketplace_model import MarketplaceReport, MarketplaceTransaction
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from fx_conversion import FXConverter
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
                str(month)+"/"+str(year),
                transaction['RedemptionOption'],
                transaction['CategoryName'],
                transaction['SubCategoryName'],
                transaction['ProductName']
            )
            report.addTransaction(tr)
        
        # apply conversion to Margin($)
        fx = FXConverter()
        report.all_transactions_frame['Margins ($)'] =report.all_transactions_frame.apply(lambda row:fx.ccy_to_cst_usd(row['Margin Amount'],row['Product Currency']),axis=1)
        report.all_transactions_frame['Amount ($)'] = report.all_transactions_frame.apply(lambda row:fx.ccy_to_cst_usd(row['Product Amount'],row['Product Currency']),axis=1)



        report.Save()





        return report    
    else:
        print("no transactions available") 
        return {} 