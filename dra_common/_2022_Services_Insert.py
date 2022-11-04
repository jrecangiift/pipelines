from product_marketplace_controller import BuildMarketplaceReport
from services_model import ServiceRevenueDeclaration, ServiceType


# List per client of all services in 2022

srd = ServiceRevenueDeclaration("Professional Services","Corporate Loyalty","this is a description", "CBI",8,2022,'123.56',"USD")
srd.Save()

