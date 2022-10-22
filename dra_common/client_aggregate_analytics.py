### build analytical cube across client and time

from cmath import nan
from dataclasses import dataclass
from multiprocessing.connection import Client
from unicodedata import decimal

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

#### GLOBAL DATA FRAMES ##########################
MAIN_FRAME_COLUMNS = ["Client","Date","Business Line","Product","Type","Identifier","Value"]
REVENUE_COLUMNS = ["Client","Date","Business Line","Product","Revenue Type","Gross Amount ($)","Net Amount ($)","Base Amount","Base Currency","All Tags","Net Offset", "Label"]
##################################################

#### LBMS DATA FRAMES ############################
ACCRUALS_COLUMNS = ["Client","Date","Channel","Product","Points Accrued ($)", "GMV ($)", "Points Expired ($)"]
REDEMPTION_COLUMNS = ["Client","Date","Redemption Option","Points Redeemed ($)","Number Transactions"]
USERS_POINTS_COLUMNS = ["Client","Date","Points Value Threashold ($)","Number Users","Points Value ($)"]
##################################################

@dataclass_json
@dataclass
class ClientsAggregateAnalytics:

    

    main_frame: pd.DataFrame = pd.DataFrame(columns=MAIN_FRAME_COLUMNS)
    revenue_frame:pd.DataFrame = pd.DataFrame(columns=REVENUE_COLUMNS)
    lbms_accruals: pd.DataFrame = pd.DataFrame(columns=ACCRUALS_COLUMNS)
    lbms_redemptions: pd.DataFrame = pd.DataFrame(columns=REDEMPTION_COLUMNS)
    lbms_users_points: pd.DataFrame = pd.DataFrame(columns=USERS_POINTS_COLUMNS)
    
    missing_data_points: List = field(default_factory=list)

    def PushReport(self,report):
        client_code = report.client_code
        date=str(report.month)+"/"+str(report.year)
        items=[]
        try:
            # Process LBMS
            if 'LBMS' in report.configuration.products:
                PROD="LBMS"
                BIZ="Corporate Loyalty"
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
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","total_points",fx.point_to_cst_usd(metrics.lbms_state.total_points))
                )
                items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_accrued",fx.point_to_cst_usd(metrics.points_accrued))
                )
                items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_redeemed",fx.point_to_cst_usd(metrics.points_redeemed))
                )
                items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","total_users",metrics.lbms_state.total_users)
                )
                items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","active_users",metrics.customers_activity.earned_points)
                )
                items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","accrual_gmv",gmv)
                )

                df_main = pd.DataFrame(items,columns=MAIN_FRAME_COLUMNS)
                self.main_frame = pd.concat([self.main_frame,df_main])

                ### Revenues
                rev_items = []
                for rev in report.revenues:
                    # Gross value
                    
                    cl = rev.classification
                    REVENUE_COLUMNS = ["Client","Date","Business Line","Product","Revenue Type","Gross Amount ($)","Net Amount ($)","Base Amount","Base Currency","All Tags","Net Offset", "Label"]
                    rev_items.append(
                    {
                        "Client":client_code,
                        "Date":date,
                        "Business Line":cl.business_line,
                        "Product":cl.product_line,
                        "Revenue Type":cl.tags["type"],
                        "Gross Amount ($)":fx.ccy_to_cst_usd(rev.amount, rev.currency_code),
                        "Net Amount ($)":fx.ccy_to_cst_usd(rev.amount, rev.currency_code)*(1-rev.net_offset),
                        "Base Amount":rev.amount,
                        "Base Currency":rev.currency_code,
                        "All Tags":cl.tags,
                        "Net Offset":rev.net_offset,
                        "Label": rev.label
                    })
                    

                ## Second Order Metrics
                df_rev = pd.DataFrame(rev_items,columns=REVENUE_COLUMNS)
                self.revenue_frame = pd.concat([self.revenue_frame,df_rev])

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

                ### push second order metrics for LBMS
                secondary_metrics_items = []

                net_revenues =  df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD)]["Net Amount ($)"].sum()
                gross_revenues = df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD) ]["Gross Amount ($)"].sum()
                take_rate = net_revenues / self.GetMetrics(client_code,date,BIZ,PROD,"accrual_gmv")
                net_revenue_per_active_user = net_revenues / self.GetMetrics(client_code,date,BIZ,PROD,"active_users")
                accrual_engagement_rate = self.GetMetrics(client_code,date,BIZ,PROD,"active_users") / self.GetMetrics(client_code,date,BIZ,PROD,"total_users")

                secondary_metrics_items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","net_revenues", net_revenues )
                )
                secondary_metrics_items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","gross_revenues", gross_revenues )
                )
                secondary_metrics_items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","take_rate", take_rate )
                )
                secondary_metrics_items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","net_revenue_per_active_user", net_revenue_per_active_user )
                )
                secondary_metrics_items.append(
                    mk_mf_item(client_code,date,BIZ,PROD,"metrics","accrual_engagement_rate", accrual_engagement_rate )
                )




                df_secondary = pd.DataFrame(secondary_metrics_items,columns=MAIN_FRAME_COLUMNS)
                self.main_frame = pd.concat([self.main_frame,df_secondary])



            # Process Other Products / Feeds

            

        except:
            traceback.print_exc()
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
    # or runs calculation for second order metrics (e.g. total net revenues which requires a different data structure)
    def GetMetrics(self,client,date,business,product,identifier):
        df_main = self.main_frame 
        return df_main[(df_main['Client']==client) & (df_main['Date']==date)& (df_main['Business Line']==business) 
        & (df_main['Product']==product)  & (df_main['Type']=='metrics') & (df_main['Identifier']==identifier)]['Value'].sum()

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