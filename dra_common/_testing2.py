from services_model import ServiceRevenueDeclaration, ServiceType


srd = ServiceRevenueDeclaration("Professional Services","Corporate Loyalty","this is a description", "CBI",8,2022,'123.56',"USD")
srd.Save()
srd = ServiceRevenueDeclaration(ServiceType.marketing,"Corporate Loyalty","this is a description", "CBI",9,2022,'0',"USD")
srd.Save()
srd = ServiceRevenueDeclaration(ServiceType.prop_offers,"Corporate Loyalty","asdasdasd", "BDI",9,2022,'987',"USD")
srd.Save()

# srds = ServiceRevenueDeclaration.ListForClient(10,2022,"CBI")

# print(srds)