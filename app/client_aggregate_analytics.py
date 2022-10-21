### build analytical cube across client and time

from cmath import nan
from dataclasses import dataclass
from multiprocessing.connection import Client
from unicodedata import decimal
from xmlrpc.client import Boolean
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict,List
from enum import Enum
from client_configuration_model import ClientConfiguration
from fx_conversion import FXConverter
from revenue_model import BusinessLine, RevenueItem
import pandas as pd
import client_aggregate_model as cam
import traceback

MAIN_FRAME_COLUMNS = ["Client","Date","Business Line","Product","Type","Identifier","Value"]

ACCRUALS_COLUMNS = ["Client","Date","Channel","Product","Points Accrued ($)", "GMV ($)", "Points Expired ($)"]
REDEMPTION_COLUMNS = ["Client","Date","Redemption Option","Points Redeemed ($)","Number Transactions"]
USERS_POINTS_COLUMNS = ["Client","Date","Points Value Threashold ($)","Number Users","Points Value ($)"]

@dataclass_json
@dataclass
class ClientsAggregateAnalytics:

    

    main_frame: pd.DataFrame = pd.DataFrame(columns=MAIN_FRAME_COLUMNS)
    lbms_accruals: pd.DataFrame = pd.DataFrame(columns=ACCRUALS_COLUMNS)
    lbms_redemptions: pd.DataFrame = pd.DataFrame(columns=REDEMPTION_COLUMNS)
    lbms_users_points: pd.DataFrame = pd.DataFrame(columns=USERS_POINTS_COLUMNS)
    
    missing_data_points: List = field(default_factory=list)

    def PushReport(self,report):
        client_code = report.client_code
        date=str(report.month)+"/"+str(report.year)
        items=[]
        try:
            # start with metrics:
            if 'LBMS' in report.configuration.products:

                fx = FXConverter(
                    point_value =report.configuration.lbms_configuration.point_value_to_local_ccy,
                    ccy_code=report.configuration.lbms_configuration.local_ccy
                )

                metrics = report.product_metrics.lbms_metrics

                points_accrual_df = metrics.GetPointsAccrualDataFrame(fx)
                points_accrual_df = points_accrual_df.sort_values(by=["Points Accrued ($)"], ascending=False) 
                gmv = points_accrual_df["GMV ($)"].sum()


                ### Top Level Metrics

                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","total_points",fx.point_to_cst_usd(metrics.lbms_state.total_points))
                )
                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","points_accrued",fx.point_to_cst_usd(metrics.points_accrued))
                )
                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","points_redeemed",fx.point_to_cst_usd(metrics.points_redeemed))
                )
                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","total_users",metrics.lbms_state.total_users)
                )
                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","active_users",metrics.customers_activity.earned_points)
                )
                items.append(
                    mk_mf_item(client_code,date,"Corporate Loyalty","LBMS","metrics","accrual_gmv",gmv)
                )

                ### Revenues
                for rev in report.revenues:
                    # Gross value
                    cl = rev.classification
                    items.append(
                    mk_mf_item(
                        client_code,
                        date,
                        cl.business_line,
                        cl.product_line,
                        "gross_revenue",
                        cl.tags["type"],
                        fx.local_to_cst_usd(rev.amount)
                    ))
                    # Net value
                    cl = rev.classification
                    items.append(
                    mk_mf_item(
                        client_code,
                        date,
                        cl.business_line,
                        cl.product_line,
                        "net_revenue",
                        cl.tags["type"],
                        fx.local_to_cst_usd(rev.amount)*Decimal(1-rev.net_offset)
                    ))

                ## Second Order Metrics
                df = pd.DataFrame(items,columns=MAIN_FRAME_COLUMNS)
                self.main_frame = pd.concat([self.main_frame,df])

                #### push to the accrual frame
                acc_items = []
                for channel in metrics.points_accrued_per_channel.keys():
                    for product in metrics.points_accrued_per_channel[channel]:
                        acc_items.append(
                            {
                                "Client":client_code,
                                "Date":date,
                                "Channel":channel,
                                "Product":product.product_code,
                                "Points Accrued ($)":fx.point_to_cst_usd(product.points_accrued),
                                "GMV ($)":fx.local_to_cst_usd(product.gmv),
                                "Points Expired ($)":fx.point_to_cst_usd(product.points_expired)
                            }
                        )


                df_accrual = pd.DataFrame(acc_items,columns = ACCRUALS_COLUMNS)
                self.lbms_accruals = pd.concat([self.lbms_accruals,df_accrual])

                #### push to the redemption frame
                red_items = []
             
                for option in metrics.points_redeemed_per_redemption_option.keys():
                    stat = metrics.points_redeemed_per_redemption_option[option]
                  
                    red_items.append(
                        {
                            "Client":client_code,
                            "Date":date,
                            "Redemption Option":option,
                            "Points Redeemed ($)":fx.point_to_cst_usd(stat.sum),
                            "Number Transactions":stat.count
                        }
                    )

        
                df_redemption = pd.DataFrame(red_items,columns = REDEMPTION_COLUMNS)
                self.lbms_redemptions = pd.concat([self.lbms_redemptions,df_redemption])

                

                #### push to user points
                up_items = []
                users_tiering = metrics.lbms_state.users_points_tiering
                points_tiering = metrics.lbms_state.points_points_tiering
                nb_items = len(users_tiering.bounds)

                for i in range(nb_items): 
                
                    up_items.append(
                        {
                            "Client":client_code,
                            "Date":date,
                            "Points Value Threashold ($)":fx.point_to_cst_usd(users_tiering.bounds[i].up),
                            "Number Users":users_tiering.bounds[i].amount,
                            "Points Value ($)":fx.point_to_cst_usd(points_tiering.bounds[i].amount)
                            
                        }
                    )
                
                up_items.append(
                    {
                        "Client":client_code,
                        "Date":date,
                        "Points Value Threashold ($)":float('inf'),
                        "Number Users":users_tiering.max_tier_amount,
                        "Points Value ($)":fx.point_to_cst_usd(points_tiering.max_tier_amount)
                            
                    }
                )

        
                df_up= pd.DataFrame(up_items,columns =USERS_POINTS_COLUMNS)
                self.lbms_users_points = pd.concat([self.lbms_users_points,df_up])





        except:
            # traceback.print_exc()
            self.missing_data_points.append((client_code,date))




    # URL is <business.product.type.identifier>
    def GetResources(self,client,date,url):
        #breakdown the url
        tokens = url.split('.')
        business = tokens[0]
        product = tokens[1]
        type = tokens[2]
        identifier = tokens[3]
        df = self.main_frame

        return df[(df['Client']==client) & (df['Date']==date) & (df['Business Line']==business) & (df['Product']==product) & (df['Type']==type) & (df['Identifier']==identifier)][['Value']]

    def GetTotalNetRevenue(self, client, date, business, product):            
        df = self.main_frame
        return df[(df['Client']==client) & (df['Date']==date)& (df['Business Line']==business) & (df['Product']==product)  & (df['Type']=='net_revenue') ]['Value']

    # metrics are 1-d per url, client and date
    # this method either reaches directly for data in main frame
    # or runs calculation for second order data
    def GetMetrics(self,client,date,business,product,identifier):
        df = self.main_frame
        url = business+"."+product+".metrics."+identifier
        if url == "Corporate Loyalty.LBMS.metrics.net_revenues":
            return df[(df['Client']==client) & (df['Date']==date)&
            (df['Business Line']==business) & (df['Product']==product) 
            & (df['Type']=='net_revenue') ]['Value'].sum()

        elif url == "Corporate Loyalty.LBMS.metrics.take_rate":
            net_revenue = self.GetMetrics(client,date,business,product,"net_revenues")
            return net_revenue / self.GetMetrics(client,date,business,product,"accrual_gmv")
        
        elif url == "Corporate Loyalty.LBMS.metrics.net_revenue_per_active_user":
            net_revenue = self.GetMetrics(client,date,business,product,"net_revenues")
            return net_revenue / self.GetMetrics(client,date,business,product,"active_users")

        elif url == "Corporate Loyalty.LBMS.metrics.accrual_engagement_rate":       
            return self.GetMetrics(client,date,business,product,"active_users") / self.GetMetrics(client,date,business,product,"total_users")
        
        else:
            return df[(df['Client']==client) & (df['Date']==date)& (df['Business Line']==business) 
            & (df['Product']==product)  & (df['Type']=='metrics') & (df['Identifier']==identifier)]['Value'].sum()

    def GetMetricsRelativePerf(self,client,date_from,date_to,business,product,identifier):
        metrics_to = self.GetMetrics(client,date_to,business,product,identifier)
        metrics_from = self.GetMetrics(client,date_from,business,product,identifier)
        if metrics_from !=0:
            return (metrics_to-metrics_from)/metrics_from
        else:
            return nan

def mk_mf_item(client_code, date,business,product,item_type,item_id,item_value):
    return {
        "Client":client_code,
        "Date":date,
        "Business Line":business,
        "Product": product,
        "Type": item_type,
        "Identifier": item_id,
        "Value":item_value
    }