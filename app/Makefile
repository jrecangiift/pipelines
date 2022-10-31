push-to-ecr:

	aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com
	docker build -t dra_frontend .
	docker tag dra_frontend:latest 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com/dra_frontend:latest
	docker push 791246685463.dkr.ecr.ap-southeast-1.amazonaws.com/dra_frontend:latest