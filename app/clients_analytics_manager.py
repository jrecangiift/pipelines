from client_configuration_model import ClientConfigurationManager
from product_lbms_model import LBMSMonthlyData
from product_marketplace_model import MarketplaceReport
from clients_analytics import ClientsAnalytics
import traceback
import pickle
import boto3
from meta_data import GetClientMapDataFrame,GetClientMapList
class ClientAnalyticsManager:


    def BuildMonthlyClientAnalytics(self, month, year):
        config_manager = ClientConfigurationManager()
        config_manager.Init()
        clients_map = GetClientMapList()
        print(clients_map)
        
        cl_analytics = ClientsAnalytics()

        for cl in clients_map:

            # Load the config
            client = cl['Client']
            print("building for: "+cl['Client'])
            
            try:
                config = config_manager.LoadConfig(client,month,year)
            except:
                cl_analytics.report_push_execution(client,month,year,"LBMS",False)
                cl_analytics.report_push_execution(client,month,year,"Marketplace",False)
                continue

            try:          
                if "LBMS" in config.products:
                    if config.lbms_configuration.mode=='no_data':
                        cl_analytics.push_lbms_no_data(config,month,year)
                        cl_analytics.report_push_execution(client,month,year,"LBMS",True)
                    else:
                        lbms_data = LBMSMonthlyData.Load(client,month,year)
                        cl_analytics.push_lbms_data(config,lbms_data)
                        cl_analytics.report_push_execution(client,month,year,"LBMS",True)
                    print("LBMS Analytics for: "+client + "/" + str(month)+ " successful")
            except:
                cl_analytics.report_push_execution(client,month,year,"LBMS",False)
                print("LBMS Analytics for: "+client + "/" + str(month)+ " failed")
                pass
               
                # while ddb is on sandbox
            try:
                if "Marketplace" in config.products:
                    marketplace_data = MarketplaceReport.Load(9,2022)
                    marketplace_data.month=month
                    marketplace_data.year=2022
                    cl_analytics.push_marketplace_data(config,marketplace_data)
                    cl_analytics.report_push_execution(client,month,year,"Marketplace",True)
                    print("Marketplace Analytics for: "+client + "/" + str(month)+ " successful")
            except:
                cl_analytics.report_push_execution(client,month,year,"Marketplace",False)
                print("Marketplace Analytics for: "+client + "/" + str(month)+ " failed")
                pass

            try:
                
                if "Services" in config.products:

                    cl_analytics.pull_services_data(config, month,year)
                    cl_analytics.report_push_execution(client,month,year,"Services",True)
                    print("Services Analytics for: "+client + "/" + str(month)+ " successful")
            except:
                traceback.print_exc()
                cl_analytics.report_push_execution(client,month,year,"Services",False)
                print("Services Analytics for: "+client + "/" + str(month)+ " failed")    
                

        self._saveMonthlyClientAnalytics(cl_analytics,month,year)

        return cl_analytics

    def _saveMonthlyClientAnalytics(self,analytics, month, year):
        bucket = 'dra-clients-analyics-serialized'
        key = str(month)+"@"+str(year)
        pickle_byte_obj = pickle.dumps(analytics)
        s3_resource = boto3.resource('s3')
        s3_resource.Object(bucket, key).put(Body=pickle_byte_obj)

        
    def LoadMonthlyClientAnalytics(self,month,year):
        bucket = 'dra-clients-analyics-serialized'
        key = str(month)+"@"+str(year)      
        s3 = boto3.resource('s3')
        return pickle.loads(s3.Bucket(bucket).Object(key).get()['Body'].read())

    def LoadClientAnalytics(self,dates) -> ClientsAnalytics:
        analytics = ClientsAnalytics()
        for date in dates:
            token = date.split('/')
            analytics_temp = self.LoadMonthlyClientAnalytics(token[0],token[1])
            analytics.concat(analytics_temp)
        return analytics

    
    def ListAll(self):
        s3_client = boto3.client('s3')
        files = s3_client.list_objects_v2(Bucket='dra-clients-analyics-serialized')
        dates = []
        if (files['KeyCount']>0):
            files_json = files['Contents']
            for fi in files_json:
                tok = fi['Key'].split('@')
                period=tok[0]+'/'+ tok[1]
                dates.append(period)
        return dates


