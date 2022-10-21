
from unicodedata import decimal
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict



@dataclass_json
@dataclass
class MarketplaceTransactionAggregate:
    total_margin: Decimal = Decimal(0)
    total_transaction_amount:Decimal = Decimal(0)
    total_transactions: int = 0

@dataclass_json
@dataclass
class CurrencyAggregates:
    aggregates: Dict[str,MarketplaceTransactionAggregate] = field(default_factory=dict)


@dataclass_json
@dataclass
class MarketPlaceReport:
    month: int 
    year: int
    clients: Dict[str, CurrencyAggregates] = field(default_factory=dict)
    suppliers: Dict[str, CurrencyAggregates] = field(default_factory=dict)

    def addSupplierTransaction(self,supplier,currency, margin, amount):
        
        if supplier not in self.suppliers:
            self.suppliers[supplier]= CurrencyAggregates()
        if currency not in self.suppliers[supplier].aggregates:
            self.suppliers[supplier].aggregates[currency] = MarketplaceTransactionAggregate()
        
        agg = self.suppliers[supplier].aggregates[currency]
        if isinstance(margin,str):
            agg.total_margin+=Decimal(margin)
        else:
            agg.total_margin+=margin
        agg.total_transaction_amount+=amount
        agg.total_transactions+=1
    
    def addClientTransaction(self,client,currency, margin, amount):
         
        if client not in self.clients:
            self.clients[client]= CurrencyAggregates()
        if currency not in self.clients[client].aggregates:
            self.clients[client].aggregates[currency] = MarketplaceTransactionAggregate()
        
        agg = self.clients[client].aggregates[currency]
        if isinstance(margin,str):
            agg.total_margin+=Decimal(margin)
        else:
            agg.total_margin+=margin
        agg.total_transaction_amount+=amount
        agg.total_transactions+=1


