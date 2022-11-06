from product_marketplace_controller import BuildMarketplaceReport
from services_model import ServiceRevenueDeclaration, ServiceType
from clients_analytics_manager import ClientAnalyticsManager
from client_configuration_model import ClientConfiguration, CLIENT_CONFIG_BUCKET, ClientConfigurationManager
from clients_analytics import ClientsAnalytics
from product_lbms_model import LBMSMonthlyData

from clients_analytics import ClientsAnalytics
from clients_analytics_manager import ClientAnalyticsManager
# srd = ServiceRevenueDeclaration("Professional Services","Corporate Loyalty","this is a description", "CBI",8,2022,'123.56',"USD")
# srd.Save()
# srd = ServiceRevenueDeclaration(ServiceType.marketing,"Corporate Loyalty","this is a description", "CBI",9,2022,'0',"USD")
# srd.Save()
# srd = ServiceRevenueDeclaration(ServiceType.prop_offers,"Corporate Loyalty","asdasdasd", "BDI",9,2022,'987',"USD")
# srd.Save()

# srds = ServiceRevenueDeclaration.ListForClient(10,2022,"CBI")

# print(srds)

config_manager = ClientConfigurationManager()
config_manager.Init()
month=5
cl='Al Masraf'

cl_analytics = ClientsAnalytics()
config = config_manager.LoadConfig(cl,month,2022)
lbms_data = LBMSMonthlyData.Load(cl,month,2022)
cl_analytics.push_lbms_data(config,lbms_data)
# marketplace_data = MarketplaceReport.Load(9,2022)
# marketplace_data.month=month
# marketplace_data.year=2022
# cl_analytics.push_marketplace_data(config,marketplace_data)
print("Loading for: "+cl + "/" + str(month)+ " successful")

