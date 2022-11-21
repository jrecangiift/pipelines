
from http import client
from unicodedata import decimal
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict
import pandas as pd
import pickle
from fx_conversion import FXConverter

MARKETPLACE_DATA_AWS = 'dra-marketplace-data-prod'


MARGINS_FRAME_COLUMNS = ["Supplier", "Client","Date", "Margin Amount", "Currency Code","Number Transactions", "Transactions Amount"]
MARKUPS_DET_FRAME_COLUMNS =  ["Supplier", "Client","Date", "Markup Amount", "Currency Code","Number Transactions", "Transactions Amount"]
ALL_TRANSACTIONS = ["Supplier","Client","Client Currency", "Client Amount", "Product Currency", "Product Amount",
"Margin Amount","Date","Redemption Option","Category","Subcategory","Product Name"]

@dataclass
class MarketplaceTransaction:
    supplier:str
    client:str
    client_ccy:str
    product_ccy:str
    client_amount:Decimal
    product_amount:Decimal
    margin_amount:Decimal
    date:str
    redemptionOption:str
    categoryName:str
    subcategoryName:str
    productName:str


@dataclass
class MarketplaceReport:
    month: int 
    year: int
    margins_frame : pd.DataFrame = pd.DataFrame(columns=MARGINS_FRAME_COLUMNS)
    markups_det_frame : pd.DataFrame = pd.DataFrame(columns=MARKUPS_DET_FRAME_COLUMNS)
    all_transactions_frame :pd.DataFrame = pd.DataFrame(columns = ALL_TRANSACTIONS)
    # clients: Dict[str, CurrencyAggregates] = field(default_factory=dict)
    # suppliers: Dict[str, CurrencyAggregates] = field(default_factory=dict)


    def addTransaction(self,tr):
        
         # temp fix the margin amount being str not Decimal
        if isinstance(tr.margin_amount,str):
            tr.margin_amount = Decimal(tr.margin_amount)
        fx_conv = FXConverter()
        #push into all transactions frame
        all_items =[]
        all_items.append({
            'Supplier':tr.supplier,
            'Client':tr.client,
            'Client Currency':tr.client_ccy,
            'Client Amount':tr.client_amount,
            'Product Currency':tr.product_ccy,
            'Product Amount':tr.product_amount,
            'Margin Amount':tr.margin_amount,
            'Date':tr.date,
            'Redemption Option':tr.redemptionOption,
            'Category':tr.categoryName,
            'Subcategory':tr.subcategoryName,
            'Product Name':tr.productName,
            # 'Margin ($)': fx_conv.ccy_to_cst_usd(amount=tr.margin_amount,ccy=tr.product_amount)
        })
        df = pd.DataFrame(all_items,columns=ALL_TRANSACTIONS)
        self.all_transactions_frame=pd.concat([self.all_transactions_frame,df], ignore_index=True)



        # PROCESS MARGINS - store all transactions then aggregate 
        df = self.margins_frame[(self.margins_frame["Supplier"]==tr.supplier) &(self.margins_frame["Client"]==tr.client) &(self.margins_frame["Currency Code"]==tr.product_ccy)]
        # no entry yet
        if len(df.index)==0:
            items = []
            items.append({
                "Supplier":tr.supplier,
                "Client": tr.client,
                "Date": tr.date,
                "Margin Amount":tr.margin_amount,
                "Currency Code":tr.product_ccy,
                "Number Transactions":1,
                "Transactions Amount":tr.product_amount
            })
            df = pd.DataFrame(items,columns=MARGINS_FRAME_COLUMNS)
            self.margins_frame=pd.concat([self.margins_frame,df], ignore_index=True)
            # self.margins_frame=self.margins_frame.reset_index(inplace=False)
        # agregate stuff
        elif len(df.index)==1:
            index = df.index
            self.margins_frame.at[(index[0],"Number Transactions")] +=1
            self.margins_frame.at[(index[0],"Margin Amount")] += tr.margin_amount
            self.margins_frame.at[(index[0],"Transactions Amount")] += tr.product_amount

        # PROCESS MARKUPS - they happen when client and product price are different
        if tr.client_ccy != tr.product_ccy:
            print("Stochastic Markups not implemented yet")
        else:
            if tr.client_amount != tr.product_amount:
                # We have a deterministic markup
                markup = tr.client_amount - tr.product_amount
                df = self.markups_det_frame[(self.markups_det_frame["Supplier"]==tr.supplier) &(self.markups_det_frame["Client"]==tr.client) &(self.markups_det_frame["Currency Code"]==tr.product_ccy)]

                if len(df.index)==0:
                    items = []
                    items.append({
                        "Supplier":tr.supplier,
                        "Client": tr.client,
                        "Date": tr.date,
                        "Markup Amount":markup,
                        "Currency Code":tr.product_ccy,
                        "Number Transactions":1,
                        "Transactions Amount":tr.product_amount
                    })
                    df = pd.DataFrame(items,columns=MARKUPS_DET_FRAME_COLUMNS)
                    self.markups_det_frame=pd.concat([self.markups_det_frame,df], ignore_index=True)
                elif len(df.index)==1:
                    index = df.index
                    self.markups_det_frame.at[(index[0],"Number Transactions")] +=1
                    self.markups_det_frame.at[(index[0],"Markup Amount")] += markup
                    self.markups_det_frame.at[(index[0],"Transactions Amount")] += tr.product_amount

    def to_json(self):
        serialized = {
            "month":self.month,
            "year":self.year,
            "margins_frame":json.dumps(self.margins_frame.to_json())
        }
        return json.dumps(serialized)

    @staticmethod
    def from_json(contents):
        dict = json.loads(contents)
        report = MarketplaceReport(0,0)
        report.month = dict["month"]
        report.year = dict["year"]
        report.margins_frame = json.loads(dict["margins_frame"])
        return report


 
    def Save(self):
        bucket = MARKETPLACE_DATA_AWS 
        key = str(self.month)+"@"+str(self.year)
        pickle_byte_obj = pickle.dumps(self)
        s3_resource = boto3.resource('s3')
        s3_resource.Object(bucket, key).put(Body=pickle_byte_obj)
        

    @staticmethod
    def Load(month, year):
        
        bucket = MARKETPLACE_DATA_AWS 
        key = str(month)+"@"+str(year)      
        s3 = boto3.resource('s3')
        return pickle.loads(s3.Bucket(bucket).Object(key).get()['Body'].read())

    @staticmethod
    def ListAll():
        s3_client = boto3.client('s3')
        files = s3_client.list_objects_v2(Bucket=MARKETPLACE_DATA_AWS)
        dates = []
        if (files['KeyCount']>0):
            files_json = files['Contents']
            for fi in files_json:
                tok = fi['Key'].split('@')
                period=tok[0]+'/'+ tok[1]
                dates.append(period)
        return dates

    