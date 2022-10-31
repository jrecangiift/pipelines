from dataclasses import dataclass, field
from decimal import Decimal
from xmlrpc.client import Boolean
from dataclasses_json import dataclass_json
from enum import Enum
from typing import Dict,List
from meta_data import BusinessLine,ProductLine

@dataclass_json
@dataclass
class RevenueClassification:
    business_line: BusinessLine = BusinessLine.unknown
    product_line: ProductLine = ProductLine.unknown
    tags: Dict[str,str] = field(default_factory=dict)

@dataclass_json
@dataclass
class RevenueItem:
    classification:RevenueClassification
    amount: Decimal = 0
    currency_code: str = ""
    label: str = ""
    net_offset: Decimal = 0


# @dataclass_json
# @dataclass
# class MonthlyRevenues:
#     month:int
#     year:int
#     revenue_items: List[RevenueItem]


