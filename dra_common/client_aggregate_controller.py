
from unicodedata import decimal
import boto3

import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict,List

from client_configuration_model import ClientConfiguration,LBMSConfiguration,RedemptionMapping,LoadClientConfig
from revenue_model import RevenueItem
import lbms_client_adapter as lbms_client_adapter
from client_aggregate_model import ClientAggregateReport, ProductMetrics
from operator import attrgetter




def _getDecimalValueFromPath(report,path):
    try:
        # @ means the accessor in a method on report - argument after #
        if "@" in path:
            tokens = path[1:].split("#")
            return Decimal(getattr(report, tokens[0])(tokens[1]))
        # straight prop
        else:
            return Decimal(attrgetter(path)(report))
    except:
        print("Could not find index path: "+ path)
        return Decimal(0)




def CalculateClientRevenues(config,report):

    ## single_fixed_revenues
    for dec in config.revenues.single_fixed_revenues:
        if dec.month == report.month and dec.year == report.year:
            item = RevenueItem(
                dec.classification,
                dec.amount,
                dec.currency_code,
                dec.label,
                dec.net_offset
            )
            item.classification.tags["frequency"] = "single"
            item.classification.tags["variability"] = "fixed"
            report.revenues.append(item)

    ## recurring_fixed_revenues
    for dec in config.revenues.recurring_fixed_revenues:
        item = RevenueItem(
            dec.classification,
            dec.amount,
            dec.currency_code,
            dec.label,
            dec.net_offset
        )
        item.classification.tags["frequency"] = "monthly"
        item.classification.tags["variability"] = "fixed"
        report.revenues.append(item)

    ## recurring_float_revenues - Linear
    for dec in config.revenues.recurring_float_revenues.linear:

 

        item = RevenueItem(
            dec.classification,
            Decimal(dec.alpha) + Decimal(dec.beta) * _getDecimalValueFromPath(report,dec.index),
            dec.currency_code,
            dec.label,
            dec.net_offset
        )

        item.classification.tags["frequency"] = "monthly"
        item.classification.tags["variability"] = "float"
        report.revenues.append(item)

    ## recurring_fixed_revenues - Linear

    for dec in config.revenues.recurring_float_revenues.min_max_linear:

        index = Decimal(attrgetter(dec.index)(report))
        beta = Decimal(dec.beta)
        alpha = Decimal(dec.alpha)
 

        linear_piece = Decimal(dec.alpha) + Decimal(dec.beta) * _getDecimalValueFromPath(report,dec.index)
        if dec.has_min and linear_piece <dec.min:
            linear_piece = dec.min
        if dec.has_max and linear_piece >dec.max:
            linear_piece = dec.max

        item = RevenueItem(
            dec.classification,
            Decimal(dec.alpha) + Decimal(dec.beta) * Decimal(attrgetter(dec.index)(report)),
            dec.currency_code,
            dec.label,
            dec.net_offset
        )
     
        item.classification.tags["frequency"] = "monthly"
        item.classification.tags["variability"] = "float"
        report.revenues.append(item)

def BuildClientReport(client,month,year):

    try:
        print("Start BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year))
        config = LoadClientConfig(client)

        report = ClientAggregateReport(client,month,year)
        report.product_metrics 

        # Calculate Product Metrics
        if 'LBMS' in config.products:
            lbms_client_adapter.UpdateClientAggregateReport(config,report)
            
        # Calculate Client Revenues - sets Revenue Items in the report
        CalculateClientRevenues(config,report)    

        # Apply the configuration used
        report.configuration=config

        # save the report 
        report.Save()
        print("Done BuildClientReport: " + client +"/"+ str(month) + "/"+ str(year))
        return report
    except:
        print("Could not BuildClientReport:" +client +"/"+ str(month) + "/"+ str(year) )
        return {}
  


