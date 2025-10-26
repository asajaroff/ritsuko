IMAGE_NAME=harbor.eencloud.com/test/ritsuko
UNIQ=$(shell git rev-parse --short HEAD)
IMAGE_TAG=v1.2.3
IMAGE_TAG_UNIQ= $(IMAGE_TAG)-$(UNIQ)
IMAGE=$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_UNIQ=$(IMAGE_NAME):$(IMAGE_TAG)-$(UNIQ)
ANTHROPIC_API_KEY=$(shell env | grep ANTHROPIC_API_KEY | cut -d'=' --fields 2)

ZULIP_SITE=$(shell cat .env | grep ZULIP_SITE | cut -d'=' -f 2)
ZULIP_EMAIL=$(shell cat .env | grep ZULIP_EMAIL | cut -d'=' -f 2)
ZULIP_API_KEY=$(shell cat .env | grep ZULIP_API_KEY | cut -d'=' -f 2)
GITHUB_MATCHOX_TOKEN=$(shell cat .env | grep GITHUB_MATCHOX_TOKEN | cut -d'=' -f 2)


.PHONY: help
.DEFAULT_GOAL=help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


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

.PHONY: run
run: build ## Runs the container locally with docker
	docker run -ti \
		-e RITSUKO_VERSION=$(IMAGE_UNIQ) \
		docker.io/$(IMAGE_UNIQ)

.PHONY: release
release: ## Updates the git tag in chart/Chart.yaml, commits it and pushes it upstream
	yq -y --in-place ".appVersion = \"$(IMAGE_TAG_UNIQ)\"" chart/Chart.yaml
	echo 'git add chart/Chart.yaml'
	echo 'git commit -m "Upadting chart appVersion to $(IMAGE_TAG_UNIQ)"'

dev: ## Runs the container locally
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		-e GITHUB_MATCHBOX_KEY=$(ZULIP_EMAIL) \
		-e GITHUB_MATCHBOX_TOKEN=$(GITHUB_MATCHBOX_TOKEN) \
		-e ZULIP_EMAIL=$(ZULIP_EMAIL) \
		-e ZULIP_API_KEY=$(ZULIP_API_KEY) \
		-e ZULIP_SITE=$(ZULIP_SITE) \
		-e LOG_LEVEL=INFO \
		$(IMAGE_UNIQ)

debug: ## Runs the container locally in debug mode
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		-e GITHUB_MATCHBOX_KEY=$(ZULIP_EMAIL) \
		-e GITHUB_MATCHBOX_TOKEN=$(GITHUB_MATCHBOX_TOKEN) \
		-e ZULIP_EMAIL=$(ZULIP_EMAIL) \
		-e ZULIP_API_KEY=$(ZULIP_API_KEY) \
		-e ZULIP_SITE=$(ZULIP_SITE) \
		-e LOG_LEVEL=DEBUG \
		$(IMAGE)


local:
	. .venv/bin/activate
	./run.sh

test: ## Run unit tests
	@if [ ! -d .venv ]; then echo "Virtual environment not found. Creating it..."; python3 -m venv .venv; .venv/bin/pip install -r src/requirements.txt; fi
	.venv/bin/python -m pytest tests/test_bot.py tests/test_fetcher.py -v

test-coverage: ## Run tests with coverage report
	@if [ ! -d .venv ]; then echo "Virtual environment not found. Creating it..."; python3 -m venv .venv; .venv/bin/pip install -r src/requirements.txt; fi
	.venv/bin/python -m pytest tests/test_bot.py tests/test_fetcher.py -v --cov=src --cov-report=term-missing

test-integration: ## Run integration tests against live bot
	@if [ ! -f tests/.env.test ]; then echo "Error: .env.test not found. Copy .env.test.example and configure it."; exit 1; fi
	./tests/run_integration_tests.sh

test-integration-verbose: ## Run integration tests with verbose output
	@if [ ! -f .env.test ]; then echo "Error: .env.test not found. Copy .env.test.example and configure it."; exit 1; fi
	./run_integration_tests.sh -v

test-all: test test-integration ## Run all tests (unit and integration)

echo:
	@echo $(IMAGE_UNIQ)
	@echo $(IMAGE_NAME):$(IMAGE_TAG)
	@echo $(IMAGE_NAME):$(IMAGE_TAG_UNIQ)
	@echo IMAGE_NAME: $(IMAGE_NAME)
	@echo UNIQ: $(UNIQ)
	@echo IMAGE_TAG: $(IMAGE_TAG)
	@echo IMAGE_TAG_UNIQ: $(IMAGE_TAG_UNIQ)
	@echo IMAGE: $(IMAGE)
	@echo IMAGE: $(IMAGE_UNIQ)
	@echo ANTHROPIC: $(ANTHROPIC_API_KEY)
	@echo $(ZULIP_SITE)
	@echo $(ZULIP_EMAIL)

HELM_RELEASE_NAME = ritsuko-make
helm-debug: ## Render the helm chart with debug information
	cd chart
	helm install ${HELM_RELEASE_NAME} \
		--dry-run \
		--debug \
		-f ./chart/values.yaml \
		chart/

helm-install: ## Installs the chart
	helm upgrade --install ${HELM_RELEASE_NAME} \
		-f ./chart/values-override.yaml \
		--set 'image.tag=${IMAGE_TAG_UNIQ}' \
		chart/

helm-uninstall: ## Installs the chart
	helm del ${HELM_RELEASE_NAME}

helm-reinstall: helm-uninstall helm-install
