from http import client
import simplejson as json
import logging
import time
import traceback
import requests
import boto3

import sys
from client_configuration_model import ClientConfiguration, CLIENT_CONFIG_BUCKET, ClientConfigurationManager
from clients_analytics import ClientsAnalytics
from clients_analytics_manager import ClientAnalyticsManager
# from product_lbms_model import LBMSMonthlyData
# from fx_conversion import FXConverter
# from revenue_model import BusinessLine, ProductLine, RevenueClassification
# from product_marketplace_model import MarketplaceReport
from product_marketplace_controller import BuildMarketplaceReport
# from boto3.dynamodb.conditions import Key
# from decimal import Decimal
# # import utils as utils
# import client_configuration_model as ccm
# from product_lbms_controller import BuildMonthlyLBMSData


report = BuildMarketplaceReport(9,2022)

print(report.margins_frame)





# import pandas as pd

# warnings.filterwarnings('ignore')

# def MakeConfigfileSample():
    # cc = ccm.ClientConfiguration("ABC",
    #                              ccm.LBMSConfiguration("IDR", 10, False), ccm.MarketplaceConfiguration(
    #                                  "BNI"), ["LBMS", "Marketplace"]
    #                              )

    # cc.revenues.single_fixed_revenues.append(ccm.SingleFixedRevenue(
    #     8,
    #     2022,
    #     amount=10000,
    #     currency_code="USD"))

    # cc.revenues.recurring_fixed_revenues.append(ccm.RecurringFixedRevenue(
    #     amount=15000,
    #     currency_code="USD",
    #     label="some stuff",
    #     net_offset=Decimal('0.01')))

    # cc.revenues.recurring_float_revenues.linear.append(ccm.FloatLinearRevenue(
    #     RevenueClassification(
    #         BusinessLine.corporate_loyalty, ProductLine.lbms),
    #     Decimal('0'),
    #     Decimal('0.01'),
    #     "product_metrics.lbms_metrics.points_accrued",
    #     "USD",
    #     "per fee something",
    #     Decimal('0.01')
    # ))

    # cc.revenues.recurring_float_revenues.min_max_linear.append(ccm.FloatMinMaxLinearRevenue(
    #     RevenueClassification(
    #         BusinessLine.corporate_loyalty, ProductLine.lbms),
    #     Decimal('0'),
    #     Decimal('0.01'),
    #     "product_metrics.lbms_metrics.points_accrued",
    #     "USD",
    #     "per fee something",
    #     Decimal('0.01'),
    #     has_min=True,
    #     min=Decimal('1000.00')
    # ))

    # ccm.WriteClientConfig(cc)

    # print(cc)

    # print(json.dumps(cc.to_dict(), sort_keys=True, indent=4))

    #print(json.dumps({"salary": Decimal("5000000.00")}))




######## LBMS Monthly Data Build ######
# config_manager = ClientConfigurationManager()
# config_manager.Init()
# clients = [
#     'BDI',
#     "BJB",
#     "BML",
#     "BNI",
#     "BRI",
#     "CBI",
#     "CBQ",
#     "commbank",
#     "EBL",
#     "GBK",
#     "QNB",
# ]

# months = [4, 5, 6, 7, 8, 9]

# for c in clients:
#     for m in months:
#         print(c + "/" + str(m))
#         try:
#             lbms_data = BuildMonthlyLBMSData(c, m, 2022)
#         except:
#             continue


# lbms_data = BuildMonthlyLBMSData('BJB',4,2022)


# cl_analytics = ClientsAnalytics()

# for cl in clients:
#     for month in months:
#         try:
#             config = config_manager.LoadConfig(cl,month,2022)
#             lbms_data = LBMSMonthlyData.Load(cl,month,2022)
#             cl_analytics.push_lbms_data(config,lbms_data)
#             marketplace_data = MarketplaceReport.Load(9,2022)
#             marketplace_data.month=month
#             marketplace_data.year=2022
#             cl_analytics.push_marketplace_data(config,marketplace_data)
#             print("Loading for: "+cl + "/" + str(month)+ " successful")
#         except:
#             traceback.print_exc()
#             print("Loading for: "+cl + "/" + str(month)+ " failed")


# cl_analytics.save()

# manager = ClientAnalyticsManager()

# manager.BuildMonthlyClientAnalytics(4,2022)
# manager.BuildMonthlyClientAnalytics(5,2022)
# manager.BuildMonthlyClientAnalytics(6,2022)
# manager.BuildMonthlyClientAnalytics(7,2022)
# manager.BuildMonthlyClientAnalytics(8,2022)
# anal = manager.BuildMonthlyClientAnalytics(9,2022)



# analytics = manager.LoadClientAnalytics(['4/2022','5/2022','6/2022','7/2022','8/2022','9/2022'])
# print(analytics.revenue_frame)

# cl_analytics = ClientsAnalytics.Load()

# print(cl_analytics.revenue_frame)


# config = config_manager.LoadConfig('BNI',7,2022)
# lbms_data = LBMSMonthlyData.Load('BNI',7,2022)
# cl_analytics.push_lbms_data(config,lbms_data)

# config = config_manager.LoadConfig('BNI',9,2022)
# lbms_data = LBMSMonthlyData.Load('BNI',9,2022)
# cl_analytics.push_lbms_data(config,lbms_data)

# mktplace_data = MarketplaceReport.Load(9,2022)
# cl_analytics.push_marketplace_data(config,mktplace_data)

# print(cl_analytics.main_frame)


# lbms_data = LBMSMonthlyData.Load('BNI',6,2022)

# cl_analytics = ClientsAnalytics()
# cl_analytics.push_lbms_data(config,lbms_data)
# #######################################

# # print(cl_analytics.get_pricing_index_value('BNI','7/2022',"all_points_redeemed"))

# print(cl_analytics.main_frame)


# report = BuildClientReport('BDI',7,2022)

# report = ClientAggregateReport.Load('BNI',8,2022)


# spotMarketplaceReport = MarketplaceReport.Load(9,2022)


# fx = FXConverter(
#     report.configuration.lbms_configuration.point_value_to_local_ccy,
#     report.configuration.lbms_configuration.local_ccy,
# )
# print(report.GetRevenuesDataFrame(fx))
# MakeConfigfileSample()


# client_list = ['BNI','BDI','BRI']
# date_list = ['',5/2022','6/2022','7/2022','8/2022','9/2022']
# ClientsAggregateAnalytics


# print(caa.missing_data_points)

# print(caa.main_frame)

# caa = ClientsAggregateAnalytics()
# report = ClientAggregateReport.Load('BNI',9,2022)

# spotMarketplaceReport = MarketplaceReport.Load(9,2022)

# caa.PushReport(report, spotMarketplaceReport)


# print(caa.revenue_frame)
# print(caa.main_frame)
# report = ClientAggregateReport.ListAll()
# print(report)


# client = 'BDI'
# BuildClientReport(client, 4,2022)
# BuildClientReport(client, 5,2022)
# BuildClientReport(client, 6,2022)
# BuildClientReport(client, 7,2022)
# BuildClientReport(client, 8,2022)
# BuildClientReport(client, 9,2022)





# report = MarketplaceReport.Load(9,2022)


# print(report)


######### Testing the config manager ##########

# BUCK = 'dra-config'


# client_config_manager = ClientConfigurationManager()
# client_config_manager.Init()

# conf = client_config_manager.LoadConfig('BNI',4,2022)
# print(conf)


# print(client_config_manager.client_files_dataframe)

# client_code = "BNI"

# s3_client = boto3.client('s3')
# key = client_code+".json"
# data = s3_client.get_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key)
# contents = data['Body'].read()
# config = ClientConfiguration.from_json(contents)
