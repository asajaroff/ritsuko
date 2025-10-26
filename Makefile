IMAGE_NAME=harbor.eencloud.com/test/ritsuko
IMAGE_TAG=v1.0.4
UNIQ=$(shell git rev-parse --short HEAD)
IMAGE=$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_UNIQ=$(IMAGE_NAME):$(IMAGE_TAG)-$(UNIQ)
ANTHROPIC_API_KEY=$(shell env | grep ANTHROPIC_API_KEY | cut -d'=' --fields 2)

.PHONY: build
build:
	docker build \
		--progress=plain \
		-t $(IMAGE) \
		-t $(IMAGE_UNIQ) \
		. 

.PHONY: push
push: build
	docker push \
		$(IMAGE_UNIQ)
		# docker.io/$(IMAGE_UNIQ) \

.PHONY: run
run: build
	docker run -ti \
		-e RITSUKO_VERSION=$(IMAGE_UNIQ) \
		docker.io/$(IMAGE_UNIQ)

release:
	docker build \
		--progress=plain \
		-t $(IMAGE) \
		-t $(IMAGE_UNIQ) \
		--build-arg RITSUKO_VERSION=$(IMAGE) \
		.
	docker push \
		docker.io/$(IMAGE) \

dev: ## Mounts the kubernetes config file
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		-e ZULIP_EMAIL="" \
		-e ZULIP_API_KEY="" \
		-e ZULIP_SITE="https://your.zulip.chat" \
		-e LOG_LEVEL=DEBUG \
		$(IMAGE)

dev-fixed:
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		$(IMAGE)

local:
	cd src && python bot.py

test: ## Run unit tests
	cd src && python -m pytest test_bot.py -v

test-coverage: ## Run tests with coverage report
	cd src && python -m pytest test_bot.py -v --cov=bot --cov-report=term-missing

echo:
	echo $(IMAGE_UNIQ)
	echo $(IMAGE_NAME):$(IMAGE_TAG)

helm-debug: ## Render the helm chart with debug information
	cd chart
	helm install ritsuko-bot \
		--dry-run \
		--debug \
		-f ./chart/values.yaml \
		chart/

helm-install: ## Installs the chart
	cd chart
	helm install ritsuko-bot \
		-f ./chart/values.yaml \
		chart/
