import csv
import codecs
import json
import boto3
import csv
import io
from client_aggregate_model import AccrualChannel, Bound, ClientAggregateReport, CustomersActivity, LBMSMetrics, LBMSState, PointsAndCount, PointsTiering, ProductAccrual, RedemptionOption
from decimal import Decimal

LBMS_DATA_FOLDER = "dra-client-usage-data-raw"


#### Client Channel to AccrualChannel Mapping ####

CHANNELS_MAPPING = {
    "Debit Card":AccrualChannel.debit_card,
    "DEBIT CARDS":AccrualChannel.debit_card,

    "Credit Card":AccrualChannel.credit_card,
    "Credit Cards":AccrualChannel.credit_card,
    "CREDIT CARDS":AccrualChannel.credit_card,
    
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

    "Echannels-SMS":AccrualChannel.e_channels,
    "Echannels-Transaction":AccrualChannel.e_channels,
    "E-CHANNEL":AccrualChannel.e_channels,
    "E-Channel":AccrualChannel.e_channels,
    "ECHANNELS":AccrualChannel.e_channels,
}

REDEMPTIONS_MAPPING = {
    "30":RedemptionOption.gift_card,
    "31":RedemptionOption.utility,
    "10":RedemptionOption.exchange,
    "5":RedemptionOption.travel,
    "6":RedemptionOption.travel,
    "11":RedemptionOption.shop,
    "19":RedemptionOption.charity,
    "9":RedemptionOption.cancelled,
    "32": RedemptionOption.game,
    "33":RedemptionOption.auction
}


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
        points_expired = int(row[6])
        
        if channel not in accruals_by_channel:
            accruals_by_channel[channel]=[]
        accruals_by_channel[channel].append(ProductAccrual(product_code,points_accrued,gmv,points_expired))
        total_points_accrued+=points_accrued

    report.product_metrics.lbms_metrics.points_accrued_per_channel = accruals_by_channel
    report.product_metrics.lbms_metrics.points_accrued = total_points_accrued

def _processRedemptions_Standard(report):
    
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'redemption.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    red_internal_cat = {}
    red_redemption_option = {}
    total_points_redeemed = 0
    for row in csvreader:
        trans_type = row[0]
        points = int(row[2])
        narration = row[4]
        loyalty_txn_type = row[10]
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
            red_internal_cat[narration].sum+=points
            red_internal_cat[narration].count+=1
            red_redemption_option[redemption_option].sum+=points
            red_redemption_option[redemption_option].count+=1

    report.product_metrics.lbms_metrics.points_redeemed= total_points_redeemed
    report.product_metrics.lbms_metrics.points_redeemed_per_internal_category = red_internal_cat
    report.product_metrics.lbms_metrics.points_redeemed_per_redemption_option =  red_redemption_option
    
def _processCustomersActivity_Standard(report):
    
    byte_content = LoadLBMSDataFile(report.client_code, report.month, report.year, 'ClientData.csv')
    data = byte_content.decode('utf-8')
    csvreader = csv.reader(io.StringIO(data))
    next(csvreader)

    custAcc = CustomersActivity()
    for row in csvreader:
        stat = int(row[0])
        value = int(row[3])
        
        if stat == 1:
            custAcc.new=value
        if stat == 3:
            custAcc.activated=value
        if stat == 6:
            custAcc.earned_points=value
        if stat == 9:
            custAcc.activated_and_earned_points=value
        if stat == 10:
            custAcc.cancelled=value
    
    report.product_metrics.lbms_metrics.customers_activity = custAcc

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
    
    for bds in state.users_points_tiering.bounds:
        state.total_users+=bds.amount
    state.total_users+=state.users_points_tiering.no_points_amount 
    state.total_users+=state.users_points_tiering.max_tier_amount

    state.total_users_with_points = state.total_users - state.users_points_tiering.no_points_amount

    report.product_metrics.lbms_metrics.lbms_state = state



def UpdateClientAggregateReport(config,report):

    _processAcrruals_Standard(report)
    _processRedemptions_Standard(report)
    _processCustomersActivity_Standard(report)
    _processState_Standard(report)

