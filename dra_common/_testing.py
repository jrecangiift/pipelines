
import simplejson as json
import logging
import time
import traceback
import requests
import boto3
from client_aggregate_model import ClientAggregateReport
from client_aggregate_analytics import ClientsAggregateAnalytics
from fx_conversion import FXConverter
from revenue_model import BusinessLine, ProductLine, RevenueClassification
from marketplace_model import MarketPlaceReport
from marketplace_controller import BuildMarketplaceReport
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import utils as utils
import client_configuration_model as ccm
from client_aggregate_controller import BuildClientReport
from operator import attrgetter

month = 9
year = 2022

def MakeConfigfileSample():
    cc = ccm.ClientConfiguration("BDI",
    ccm.LBMSConfiguration("IDR",10,False),["LBMS","Marketplace"])
    
    cc.revenues.single_fixed_revenues.append(ccm.SingleFixedRevenue(
        8,
        2022,
        amount=10000,
        currency_code="USD"))

    cc.revenues.recurring_fixed_revenues.append(ccm.RecurringFixedRevenue(
        amount=15000,
        currency_code="USD",
        label="some stuff",
        net_offset = Decimal('0.01')))

    cc.revenues.recurring_float_revenues.linear.append(ccm.FloatLinearRevenue(
        RevenueClassification(BusinessLine.corporate_loyalty,ProductLine.lbms),
        Decimal('0'),
        Decimal('0.01'),
        "product_metrics.lbms_metrics.points_accrued",
        "USD",
        "per fee something",
        Decimal('0.01')
    ))

    cc.revenues.recurring_float_revenues.min_max_linear.append(ccm.FloatMinMaxLinearRevenue(
        RevenueClassification(BusinessLine.corporate_loyalty,ProductLine.lbms),
        Decimal('0'),
        Decimal('0.01'),
        "product_metrics.lbms_metrics.points_accrued",
        "USD",
        "per fee something",
        Decimal('0.01'),
        has_min = True,
        min=Decimal('1000.00')
    ))


    ccm.WriteClientConfig(cc)
    

    print(cc)

    print(json.dumps(cc.to_dict(),sort_keys=True, indent=4))

    #print(json.dumps({"salary": Decimal("5000000.00")}))





# report = BuildClientReport('BDI',7,2022)

# report = ClientAggregateReport.Load('BNI',8,2022)

# fx = FXConverter(
#     report.configuration.lbms_configuration.point_value_to_local_ccy,
#     report.configuration.lbms_configuration.local_ccy,
# )
# print(report.GetRevenuesDataFrame(fx))
# MakeConfigfileSample()


# client_list = ['BNI','BDI','BRI']
# date_list = ['5/2022','6/2022','7/2022','8/2022','9/2022']
# ClientsAggregateAnalytics



# print(caa.missing_data_points)

# print(caa.main_frame)

# caa = ClientsAggregateAnalytics()
# report = ClientAggregateReport.Load('BNI',8,2022)
# caa.PushReport(report)

# report = ClientAggregateReport.ListAll()
# print(report)
client = 'BRI'
BuildClientReport(client, 4,2022)
BuildClientReport(client, 5,2022)
BuildClientReport(client, 6,2022)
BuildClientReport(client, 7,2022)
BuildClientReport(client, 8,2022)
BuildClientReport(client, 9,2022)

# report = BuildMarketplaceReport(month,year)
# print(report)
# print(json.dumps(report.to_dict(), sort_keys=True, indent=4, cls=common.JSONEncoder))

      