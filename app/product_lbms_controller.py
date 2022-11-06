
from unicodedata import decimal
import boto3

import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict,List
import traceback
from client_configuration_model import ClientConfiguration,ClientConfigurationManager
from product_lbms_model import LBMSMonthlyData,AccrualChannel, RedemptionOption
from revenue_model import RevenueItem
from product_lbms_model import AccrualChannel, Bound, CustomersActivity, LBMSMetrics, LBMSState, PointsAndCount, PointsTiering, ProductAccrual, RedemptionOption
from operator import attrgetter
import csv
import io

LBMS_DATA_FOLDER = "dra-client-usage-data-raw"

CHANNELS_MAPPING = {
    "Debit Card":AccrualChannel.debit_card,
    "DEBIT CARDS":AccrualChannel.debit_card,
    "Visa Debit":AccrualChannel.debit_card,

    "Credit Card":AccrualChannel.credit_card,
    "Credit Cards":AccrualChannel.credit_card,
    "CREDIT CARDS":AccrualChannel.credit_card,
    "Ladies Credit Card":AccrualChannel.credit_card,
    
    "Investment":AccrualChannel.investment,

    "Mortgage Loan":AccrualChannel.lending,
    "Personal Loan":AccrualChannel.lending,
    "SME Lending":AccrualChannel.lending,

    "Bancassurance":AccrualChannel.insurance,

    "CASA":AccrualChannel.casa,
    "SAVING ACCOUNT":AccrualChannel.casa,
    "Savings Account":AccrualChannel.casa,
    "Saving Account":AccrualChannel.casa,
    "Current Account":AccrualChannel.casa,
    "Term Deposits":AccrualChannel.casa,
    "Fixed Deposits":AccrualChannel.casa,

    "Echannels-SMS":AccrualChannel.e_channels,
    "Echannels-Transaction":AccrualChannel.e_channels,
    "E-CHANNEL":AccrualChannel.e_channels,
    "E-Channel":AccrualChannel.e_channels,
    "ECHANNELS":AccrualChannel.e_channels,
    "Mobile Banking":AccrualChannel.e_channels,

    "WEALTH MANAGEMENT":AccrualChannel.wealth_management,

    "MANUAL TRANSACTION":AccrualChannel.manual,
    "Default Bonus":AccrualChannel.manual,
    "Private Banking Bonus":AccrualChannel.manual,
    "Tamayuz Banking Bonus":AccrualChannel.manual,
}

REDEMPTIONS_MAPPING = {
    "30":RedemptionOption.gift_card,
    "31":RedemptionOption.utility,
    "10":RedemptionOption.exchange,
    "5":RedemptionOption.flight,
    "6":RedemptionOption.hotel,
    "11":RedemptionOption.clients_merchant,
    "21":RedemptionOption.clients_merchant,
    "19":RedemptionOption.charity,
    "9":RedemptionOption.cancelled,
    "32": RedemptionOption.game,
    "33":RedemptionOption.auction,
    "14":RedemptionOption.cashback,
    "23":RedemptionOption.travel,
    "17":RedemptionOption.gift_card,
    "3":RedemptionOption.external,
    "35":RedemptionOption.external,
    "34":RedemptionOption.external,
    "36":RedemptionOption.external,
    "37":RedemptionOption.external,
    "56":RedemptionOption.external,
    "8":RedemptionOption.reversal,
    "7":RedemptionOption.car

}

LBMS_CONTROLLER_CODE_MAPPING = {
    "FULL":[
        "Al Masraf",
        'BDI',
        'BJB',
        'BML',
        'BNI',
        'BRI',
        'CBI',
        'CBQ',
        'EBL',
        'GBK',
        'MTB',
        'QIB',
        'QNB',
        'cardbuzz',
        'commbank'
    ],
    "RED_AND_STAT":[
        'TBO'
    ],
    "RED_ONLY":[
        'Al Maryah'
    ]
}


def BuildMonthlyLBMSData(client,month,year):

    if client in LBMS_CONTROLLER_CODE_MAPPING["FULL"]:
        try:
            print("Start BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year) + " - FULL MODE")

            lbms_data = LBMSMonthlyData(client,month,year)

            _processAcrruals_Standard(lbms_data)
            _processRedemptions_Standard(lbms_data)
            
            _processState_Standard(lbms_data)
            _processCustomersActivity_Standard(lbms_data)
            
            # save the report 

            
            lbms_data.Save()
            print("Done BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year))
            return lbms_data
        except:
            traceback.print_exc()
            print("Could not BuildClientReport:" +client +"/"+ str(month) + "/"+ str(year) )
            return {}
    
    elif client in LBMS_CONTROLLER_CODE_MAPPING["RED_AND_STAT"]:
        try:
            print("Start BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year) + " - RED_AND_STAT MODE")

            lbms_data = LBMSMonthlyData(client,month,year)

           
            _processRedemptions_Standard(lbms_data)
            
            lbms_data.metrics.lbms_state = LBMSState()
            _processCustomersActivity_Standard(lbms_data)
            
            # save the report 

            
            lbms_data.Save()
            print("Done BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year))
            return lbms_data
        except:
            traceback.print_exc()
            print("Could not BuildClientReport:" +client +"/"+ str(month) + "/"+ str(year) )
            return {}
    
    elif client in LBMS_CONTROLLER_CODE_MAPPING["RED_ONLY"]:
        try:
            print("Start BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year) + " - RED_AND_STAT MODE")

            lbms_data = LBMSMonthlyData(client,month,year)

           
            _processRedemptions_Standard(lbms_data)
            
          
            # save the report 

            
            lbms_data.Save()
            print("Done BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year))
            return lbms_data
        except:
            traceback.print_exc()
            print("Could not BuildClientReport:" +client +"/"+ str(month) + "/"+ str(year) )
            return {}
    
    else:
        print("Not loading LBMS Data for: "+ client +"/"+ str(month) + "/"+ str(year))



def LoadLBMSDataFile(client_code, month,year,file):

    s3_client = boto3.client('s3')
    key = client_code+'/'+str(year)+'/'+str(month)+'/'+file
    data = s3_client.get_object(Bucket=LBMS_DATA_FOLDER, Key=key)
    contents = data['Body'].read()
    return contents


def _processAcrruals_Standard(report):
    
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'GMVProduct.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    accruals_by_channel = {}
    total_points_accrued = 0
    for row in csvreader:
        product_code = row[1]
        
        channel = AccrualChannel.unknown
        if row[2] in CHANNELS_MAPPING:
            channel = CHANNELS_MAPPING[row[2]]
        else:
            print("Unknown Channel: "+row[2])
        gmv = Decimal(row[4])
        points_accrued = int(row[5])
        # points_expired = int(row[6])
        points_expired =0
        
        if channel not in accruals_by_channel:
            accruals_by_channel[channel]=[]
        accruals_by_channel[channel].append(ProductAccrual(product_code,points_accrued,gmv,points_expired))
        total_points_accrued+=points_accrued

    report.metrics.points_accrued_per_channel = accruals_by_channel
    report.metrics.points_accrued = total_points_accrued

def _processRedemptions_Standard(report):
    
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'redemption.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    red_internal_cat = {}
    red_redemption_option = {}
    total_points_redeemed = 0
    total_fiats_spent = 0
    for row in csvreader:
        
        loyalty_txn_type = "9999"
        if len(row)==0:
            break
        
        loyalty_txn_type = row[len(row)-1]

        trans_type = row[0]
        points = int(row[2])
        fiats = Decimal(row[3])
        narration = row[4]
        redemption_option = RedemptionOption.unknown
        if loyalty_txn_type in REDEMPTIONS_MAPPING:
            redemption_option = REDEMPTIONS_MAPPING[loyalty_txn_type]
        elif loyalty_txn_type !="9":
            
            print("Unknown redemption option: " +narration+ " / "+ loyalty_txn_type)

        if loyalty_txn_type !="9":

            if narration not in red_internal_cat:
                red_internal_cat[narration]=PointsAndCount()
            if redemption_option not in red_redemption_option:
                red_redemption_option[redemption_option]=PointsAndCount()
            
            total_points_redeemed += points
            total_fiats_spent += fiats
            red_internal_cat[narration].sum+=points
            red_internal_cat[narration].fiats+=fiats
            red_internal_cat[narration].count+=1

            red_redemption_option[redemption_option].sum+=points
            red_redemption_option[redemption_option].fiats+=fiats
            red_redemption_option[redemption_option].count+=1

    report.metrics.points_redeemed= total_points_redeemed
    report.metrics.fiats_spent=total_fiats_spent
    # print ("FIATS SPENT = "+ str(total_fiats_spent))
    report.metrics.points_redeemed_per_internal_category = red_internal_cat
    report.metrics.points_redeemed_per_redemption_option =  red_redemption_option
    
def _processCustomersActivity_Standard(report):
    
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'ClientData.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    custAcc = CustomersActivity()
    total_uploaded = 0
    total_concelled =0
    total_user_with_points =0

    for row in csvreader:
        if len(row)==0:
            break
        stat = int(row[0])
        value = int(row[3])
        
        if stat == 1:
            custAcc.new=value
        if stat==2:
            total_uploaded = value
        if stat == 3:
            custAcc.activated=value
        if stat == 6:
            custAcc.earned_points=value
        if stat == 7:
            total_user_with_points = value
        if stat == 9:
            custAcc.activated_and_earned_points=value
        if stat == 10:
            custAcc.cancelled=value
        if stat == 11:
            total_cancelled = value


    report.metrics.customers_activity = custAcc

    #update state
    report.metrics.lbms_state.total_users += total_uploaded - total_cancelled
    
    report.metrics.lbms_state.total_users_with_points += total_user_with_points
    

def _processState_Standard(report):
    
    state = LBMSState()

    # Points
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'tieringpoint.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    tiering = PointsTiering()
    lineNumber = 1
    for row in csvreader:
        tokens = row[0].split(" ")
        value = int(row[1])

        if lineNumber==1:
            tiering.no_points_amount = value
         
        elif lineNumber > 1 and lineNumber < 14:
            bound = Bound()
            bound.low = int(tokens[1])
            bound.up = int(tokens[3])
            bound.amount=value
            tiering.bounds.append(bound)

        elif lineNumber==14:
            tiering.max_tier_amount = value 
            tiering.max_tier_value = int(tokens[2])
    
        lineNumber+=1
    
    state.points_points_tiering = tiering

    # Users
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'tieringuser.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    tiering = PointsTiering()
    lineNumber = 1
    for row in csvreader:
        if len(row)==0:
            break
        tokens = row[0].split(" ")
        value = int(row[1])

        if lineNumber==1:
            tiering.no_points_amount = value
         
        elif lineNumber > 1 and lineNumber < 14:
            bound = Bound()
            bound.low = int(tokens[1])
            bound.up = int(tokens[3])
            bound.amount=value
            tiering.bounds.append(bound)

        elif lineNumber==14:
            tiering.max_tier_amount = value 
            tiering.max_tier_value = int(tokens[2])
    
        lineNumber+=1
    
    state.users_points_tiering= tiering

    # Calculate Aggregates

    for bds in state.points_points_tiering.bounds:
        state.total_points+=bds.amount
    state.total_points+=state.points_points_tiering.no_points_amount 
    state.total_points+=state.points_points_tiering.max_tier_amount
    
    # done in the customer activity function

    # for bds in state.users_points_tiering.bounds:
    #     state.total_users+=bds.amount
    # state.total_users+=state.users_points_tiering.no_points_amount 
    # state.total_users+=state.users_points_tiering.max_tier_amount

    # state.total_users_with_points = state.total_users - state.users_points_tiering.no_points_amount

    report.metrics.lbms_state = state



def UpdateClientAggregateReport(config,report):

    _processAcrruals_Standard(report)
    _processRedemptions_Standard(report)
    
    _processState_Standard(report)

    # we complete the state with user metrics taken from customer activithy
    _processCustomersActivity_Standard(report)

