from dataclasses import dataclass, field
from decimal import Decimal
from xmlrpc.client import Boolean
from dataclasses_json import dataclass_json
from enum import Enum
from typing import Dict,List

class BusinessLine(str,Enum):
    corporate_loyalty = "Corporate Loyalty"
    merchant_loyalty = "Merchant Loyalty"
    employee_reward = "Employee Loyalty"
    unknown = "Unknown"

class ProductLine(str,Enum):
    lbms = "LBMS"
    marketplace = "Marketplace"
    box = "Box"
    marketing = "Marketing"
    plum = "Plum"
    unknown = "Unknown"

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


