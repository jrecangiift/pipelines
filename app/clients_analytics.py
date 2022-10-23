### build analytical cube across client and time

from cmath import nan
from dataclasses import dataclass
from multiprocessing.connection import Client
from typing_extensions import Self
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
import product_lbms_model as cam
import product_marketplace_model as mm
import traceback




#### GLOBAL DATA FRAMES ##########################
MAIN_FRAME_COLUMNS = ["Client","Date","Business Line","Product","Type","Identifier","Value"]
REVENUE_COLUMNS = ["Client","Date","Business Line","Product","Revenue Type","Gross Amount ($)","Net Amount ($)","Base Amount","Base Currency","All Tags","Net Offset", "Label"]
##################################################

#### LBMS DATA FRAMES ############################
ACCRUALS_COLUMNS = ["Client","Date","Channel","Product","Points Accrued ($)", "GMV ($)", "Points Expired ($)"]
REDEMPTION_COLUMNS = ["Client","Date","Redemption Option","Points Redeemed","Points Redeemed ($)","Number Transactions"]
USERS_POINTS_COLUMNS = ["Client","Date","Points Value Threashold ($)","Number Users","Points Value ($)"]
##################################################

#### MARKETPLACE DATA FRAMES ############################
MARGINS_COLUMNS = mm.MARGINS_FRAME_COLUMNS.append(["Margin ($)", "Transaction Amount ($)"])
MARKUPS_COLUMNS = mm.MARKUPS_DET_FRAME_COLUMNS.append(["Margin ($)", "Transaction Amount ($)"])
##################################################




@dataclass_json
@dataclass
class ClientsAnalytics:

    

    main_frame: pd.DataFrame = pd.DataFrame(columns=MAIN_FRAME_COLUMNS)
    revenue_frame:pd.DataFrame = pd.DataFrame(columns=REVENUE_COLUMNS)
    
    lbms_accruals: pd.DataFrame = pd.DataFrame(columns=ACCRUALS_COLUMNS)
    lbms_redemptions: pd.DataFrame = pd.DataFrame(columns=REDEMPTION_COLUMNS)
    lbms_users_points: pd.DataFrame = pd.DataFrame(columns=USERS_POINTS_COLUMNS)

    marketplace_margins: pd.DataFrame = pd.DataFrame(columns=MARGINS_COLUMNS)
    marketplace_markups_det: pd.DataFrame = pd.DataFrame(columns=MARKUPS_COLUMNS)
    
    missing_data_points: List =  field(default_factory=list)


    def push_lbms_data(self,client_config,data):
        month=data.month
        year=data.year

        self.lbms_process_data(client_config,data)
        
        self.lbms_calculate_revenues(client_config,month,year)

        self.lbms_finalize_metrics(client_config,month,year)
        
            
    def push_marketplace_data(self, client_config, data):        
        month=data.month
        year=data.year

        self.marketplace_process_data(client_config,data)
       
        self.marketplace_calculate_revenues(client_config,month,year)

        self.marketplace_finalize_metrics(client_config,month,year)



        #         # calculate metrics and revenues - no config at the moment - vanilla

        #         # Marketplace Revenues

       
        #         # Key marketplace metrics

        #         ])


        #     except:
        #         raise Exception("Could not process the marketplace report")

        #     # here we basically filter on marketplace client code at source, then replace with client code.

            

        # Process Other Products / Feeds


            


            





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



    #used to access data in the lbms frames of anytics. Used for pricing for client config
    # format is function.attribute
    # must support all revenue declarations for floating index based cashflows
    def get_pricing_index_value(self,client,date,index):
        token = index.split('.')
        func = token[0]
        

        if func == "points_redeemed":
            argument = token[1]
            df = self.lbms_redemptions
            return df[(df['Client']==client) & (df['Date']==date) & (df['Redemption Option']==argument)]["Points Redeemed"].sum()   

        if func == "all_points_redeemed":
            df = self.lbms_redemptions
            return df[(df['Client']==client) & (df['Date']==date)]["Points Redeemed"].sum()   

        if func == "accrual_active_users":
            return self.GetMetrics(client,date,"Corporate Loyalty","LBMS","accrual_active_users")



    def lbms_process_data(self,client_config, data):

        client_code = client_config.client_code
        date=str(data.month)+"/"+str(data.year)
        
        try:
            PROD="LBMS"
            BIZ="Corporate Loyalty"
            # set the FX converter from client's point value and local ccy
            fx = FXConverter(
                point_value =client_config.lbms_configuration.point_value_to_local_ccy,
                ccy_code=client_config.lbms_configuration.local_ccy
            )
            ### Top Level Metrics
            metrics = data.metrics

            points_accrual_df = metrics.GetPointsAccrualDataFrame(fx)
            points_accrual_df = points_accrual_df.sort_values(by=["Points Accrued ($)"], ascending=False) 
            gmv = points_accrual_df["GMV ($)"].sum()
            items=[]
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","total_points",metrics.lbms_state.total_points))
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_accrued",metrics.points_accrued))         
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_redeemed",metrics.points_redeemed))
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","total_points_std_usd",fx.point_to_cst_usd(metrics.lbms_state.total_points)))
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_accrued_std_usd",fx.point_to_cst_usd(metrics.points_accrued)))           
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","points_redeemed_std_usd",fx.point_to_cst_usd(metrics.points_redeemed)))                      
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","total_users",metrics.lbms_state.total_users))        
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","accrual_active_users",metrics.customers_activity.earned_points))        
            items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","accrual_gmv",gmv))

            df_main = pd.DataFrame(items,columns=MAIN_FRAME_COLUMNS)
            self.main_frame = pd.concat([self.main_frame,df_main])      

            #### push to the accrual frame
            acc_items = []
            for channel in metrics.points_accrued_per_channel.keys():
                for product in metrics.points_accrued_per_channel[channel]:
                    acc_items.append(
                        {
                            "Client":client_code,
                            "Date":date,
                            "Channel":channel.value,
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
                        "Points Redeemed":stat.sum,
                        "Points Redeemed ($)":fx.point_to_cst_usd(stat.sum),
                        "Number Transactions":stat.count
                    }
                )

            df_redemption = pd.DataFrame(red_items,columns =REDEMPTION_COLUMNS)
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
            traceback.print_exc()
            self.missing_data_points.append((client_code,date))

    def lbms_calculate_revenues(self,client_config, month,year):
        client = client_config.client_code
        date = str(month)+'/'+str(year)
        
        ### Revenues - calculate revenues from the lbms data and client config revenue declaration
        rev_items = []
        # Single Fixed Revenue - throw an error. LBMS product does not incur single fixed (put under services)
        
        
        fx = FXConverter(
                point_value =client_config.lbms_configuration.point_value_to_local_ccy,
                ccy_code=client_config.lbms_configuration.local_ccy
            )

        for dec in client_config.revenues.recurring_fixed_revenues:        
            cl = dec.classification
            if cl.product_line == "LBMS":
                cl.tags["frequency"] = "monthly"
                cl.tags["variability"] = "fixed"
                rev_items.append(
                {
                    "Client":client,
                    "Date":date,
                    "Business Line":cl.business_line.value,
                    "Product":cl.product_line.value,
                    "Revenue Type":cl.tags["type"],
                    "Gross Amount ($)":fx.ccy_to_cst_usd(dec.amount, dec.currency_code),
                    "Net Amount ($)":fx.ccy_to_cst_usd(dec.amount, dec.currency_code)*(1-dec.net_offset),
                    "Base Amount":dec.amount,
                    "Base Currency":dec.currency_code,
                    "All Tags":cl.tags,
                    "Net Offset":dec.net_offset,
                    "Label": dec.label
                })

        for dec in client_config.revenues.recurring_float_revenues.linear:        
            cl = dec.classification
            if cl.product_line == "LBMS":
                cl.tags["frequency"] = "monthly"
                cl.tags["variability"] = "float"
               
                index_value = self.get_pricing_index_value(client,date,dec.index)
                base_amount = Decimal(dec.alpha) + Decimal(dec.beta) * index_value

                rev_items.append(
                {
                    "Client":client_config.client_code,
                    "Date":str(month)+'/'+str(year),
                    "Business Line":cl.business_line.value,
                    "Product":cl.product_line.value,
                    "Revenue Type":cl.tags["type"],
                    "Gross Amount ($)":fx.ccy_to_cst_usd(base_amount, dec.currency_code),
                    "Net Amount ($)":fx.ccy_to_cst_usd(base_amount, dec.currency_code)*(1-dec.net_offset),
                    "Base Amount":base_amount,
                    "Base Currency":dec.currency_code,
                    "All Tags":cl.tags,
                    "Net Offset":dec.net_offset,
                    "Label": dec.label
                })

        for dec in client_config.revenues.recurring_float_revenues.min_max_linear:        
            cl = dec.classification
            if cl.product_line == "LBMS":
                cl.tags["frequency"] = "monthly"
                cl.tags["variability"] = "float"
                
                index_value = self.get_pricing_index_value(client,date,dec.index)
                linear_piece = Decimal(dec.alpha) + Decimal(dec.beta) * index_value
                
                base_amount = linear_piece
                if dec.has_min and linear_piece <dec.min:
                    base_amount = dec.min
                if dec.has_max and linear_piece >dec.max:
                    base_amount = dec.max
                
                rev_items.append(
                {
                    "Client":client_config.client_code,
                    "Date":str(month)+'/'+str(year),
                    "Business Line":cl.business_line.value,
                    "Product":cl.product_line.value,
                    "Revenue Type":cl.tags["type"],
                    "Gross Amount ($)":fx.ccy_to_cst_usd(base_amount, dec.currency_code),
                    "Net Amount ($)":fx.ccy_to_cst_usd(base_amount, dec.currency_code)*(1-dec.net_offset),
                    "Base Amount":base_amount,
                    "Base Currency":dec.currency_code,
                    "All Tags":cl.tags,
                    "Net Offset":dec.net_offset,
                    "Label": dec.label
                })

                
        df_rev = pd.DataFrame(rev_items,columns=REVENUE_COLUMNS)
        self.revenue_frame = pd.concat([self.revenue_frame,df_rev])
                   
    def lbms_finalize_metrics(self,client_config, month,year):
        
        client_code = client_config.client_code
        date=str(month)+"/"+str(year)
        BIZ = "Corporate Loyalty"
        PROD="LBMS"
        df_rev = self.revenue_frame
        ### push second order metrics for LBMS
        secondary_metrics_items = []

        net_revenues =  df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD)]["Net Amount ($)"].sum()
        gross_revenues = df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD) ]["Gross Amount ($)"].sum()
        take_rate = net_revenues / self.GetMetrics(client_code,date,BIZ,PROD,"accrual_gmv")
        net_revenue_per_active_user = net_revenues / self.GetMetrics(client_code,date,BIZ,PROD,"accrual_active_users")
        accrual_engagement_rate = self.GetMetrics(client_code,date,BIZ,PROD,"accrual_active_users") / self.GetMetrics(client_code,date,BIZ,PROD,"total_users")

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

    def marketplace_process_data(self,client_config, data):

        client_code = client_config.client_code
        PROD="Marketplace"
        BIZ="Corporate Loyalty"
        try:
            
            fx = FXConverter(
                point_value =client_config.lbms_configuration.point_value_to_local_ccy,
                ccy_code=client_config.lbms_configuration.local_ccy
            )

            marketplace_client_code = client_config.marketplace_configuration.marketplace_code
            # margins 
        
            df_margins = data.margins_frame
            self.marketplace_margins = df_margins[df_margins['Client']==marketplace_client_code]
            self.marketplace_margins['Client'] = self.marketplace_margins['Client'].replace(marketplace_client_code, client_code)
            self.marketplace_margins["Margin ($)"] = self.marketplace_margins.apply(lambda row: fx.ccy_to_cst_usd(row["Margin Amount"],row["Currency Code"]),axis=1)
            self.marketplace_margins["Transactions Amount ($)"] = self.marketplace_margins.apply(lambda row: fx.ccy_to_cst_usd(row["Transactions Amount"],row["Currency Code"]),axis=1)
            #markups
            df_markups = data.markups_det_frame
            self.marketplace_markups_det = df_markups[df_markups['Client']==marketplace_client_code]
            self.marketplace_markups_det['Client'] = self.marketplace_markups_det['Client'].replace(marketplace_client_code, client_code)
            self.marketplace_markups_det["Markup ($)"] = self.marketplace_markups_det.apply(lambda row: fx.ccy_to_cst_usd(row["Markup Amount"],row["Currency Code"]),axis=1)
            self.marketplace_markups_det["Transactions Amount ($)"] = self.marketplace_markups_det.apply(lambda row: fx.ccy_to_cst_usd(row["Transactions Amount"],row["Currency Code"]),axis=1)

        except:
            raise Exception("Could not process the marketplace report")

    def marketplace_calculate_revenues(self,client_config, month,year):    
        #margins and markups
        
        client_code = client_config.client_code
        date=str(month)+"/"+str(year)
        BIZ = "Corporate Loyalty"
        PROD="Marketplace"
        rev_items = []
        total_margins_cst_usd = self.marketplace_margins["Margin ($)"].sum()
        rev_items.append(
            {
                "Client":client_code,
                "Date":date,
                "Business Line":BIZ,
                "Product":PROD,
                "Revenue Type":"marketplace_margins",
                "Gross Amount ($)":total_margins_cst_usd,
                "Net Amount ($)":total_margins_cst_usd,
                "Base Amount":"",
                "Base Currency":"",
                "All Tags":"",
                "Net Offset":0,
                "Label": "Monthly Margins from Suppliers"
            })
        total_markups_cst_usd = max(self.marketplace_markups_det["Markup ($)"].sum(),0)
        rev_items.append(
            {
                "Client":client_code,
                "Date":date,
                "Business Line":BIZ,
                "Product":PROD,
                "Revenue Type":"marketplace_markups",
                "Gross Amount ($)":total_markups_cst_usd,
                "Net Amount ($)":total_markups_cst_usd,
                "Base Amount":"",
                "Base Currency":"",
                "All Tags":"",
                "Net Offset":0,
                "Label": "Monthly Markups from Suppliers"
            })

        # Other declared revenues in config

        df_rev = pd.DataFrame(rev_items,columns=REVENUE_COLUMNS)
        self.revenue_frame = pd.concat([self.revenue_frame,df_rev])

    def marketplace_finalize_metrics(self,client_config, month,year):
        
        client_code = client_config.client_code
        date=str(month)+"/"+str(year)
        BIZ = "Corporate Loyalty"
        PROD="Marketplace"
        df_rev = self.revenue_frame

        net_revenues =  df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD)]["Net Amount ($)"].sum()
        gross_revenues = df_rev[(df_rev['Client']==client_code) & (df_rev['Date']==date)&(df_rev['Business Line']==BIZ) & (df_rev['Product']==PROD) ]["Gross Amount ($)"].sum()
        transactions_gmv = self.marketplace_margins["Transactions Amount ($)"].sum()
        transactions_count = self.marketplace_margins["Number Transactions"].sum()
        total_margins_cst_usd = self.marketplace_margins["Margin ($)"].sum()
        total_markups_cst_usd = max(self.marketplace_markups_det["Markup ($)"].sum(),0)

        items = []
        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","net_revenues", net_revenues ))

        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","gross_revenues", gross_revenues ))
        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","transactions_gmv", transactions_gmv ))
        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","transactions_count", transactions_count ))
        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","margins_rate", total_margins_cst_usd/transactions_gmv ))
        items.append(mk_mf_item(client_code,date,BIZ,PROD,"metrics","markups_rate", total_markups_cst_usd/transactions_gmv ))

        df_secondary = pd.DataFrame(items,columns=MAIN_FRAME_COLUMNS)
        self.main_frame = pd.concat([self.main_frame,df_secondary])



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
