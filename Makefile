push-shared:

	cp dra_common/clients_analytics.py app/
	cp dra_common/clients_analytics_manager.py app/

	cp dra_common/client_configuration_model.py app/
	cp dra_common/product_lbms_controller.py app/
	cp dra_common/product_lbms_model.py app/
	cp dra_common/product_marketplace_controller.py app/
	cp dra_common/product_marketplace_model.py app/
	cp dra_common/services_model.py app/
	cp dra_common/fx_conversion.py app/
	cp dra_common/revenue_model.py app/
	cp dra_common/services_model.py app/
	cp dra_common/meta_data.py app/
	cp dra_common/utils.py app/

push-frontend-to-prod:

	aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com
	docker build -f app/Dockerfile -t dra_frontend .
	docker tag dra_frontend:latest 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com/dra_frontend:latest
	docker push 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com/dra_frontend:latest

