from dataclasses import dataclass
from decimal import Decimal

CONSTANT_FX={
    "IDR":Decimal('0.000067'),
    "AED":Decimal('0.35'),
    "USD":Decimal('1'),
    "QAR":Decimal('0.27'),
    "BDT":Decimal('0.0096'),
    "LKR":Decimal('0.0028'),
    "OMR":Decimal('2.60'),
    "MVR":Decimal('0.65'),
    "INR":Decimal('0.012'),
    "KWD":Decimal('3.23')
}

@dataclass
class FXConverter:
    point_value:Decimal = 0
    ccy_code:str = "USD"

    def local_to_cst_usd(self, amount):
        return Decimal(CONSTANT_FX[self.ccy_code])*Decimal(amount)

    def point_to_cst_usd(self, amount):
        return self.point_value*Decimal(CONSTANT_FX[self.ccy_code])*Decimal(amount)
