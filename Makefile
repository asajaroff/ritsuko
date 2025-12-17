IMAGE_NAME=ritsuko
UNIQ=$(shell git rev-parse --short HEAD)

# Generate version from git describe, fallback to v0.0.0-<hash> if no tags
GIT_VERSION=$(shell git describe --tags --always 2>/dev/null || echo "v0.0.0-$(UNIQ)")
VERSION=$(GIT_VERSION)

# Keep IMAGE_TAG for backward compatibility but derive from VERSION
IMAGE_TAG=$(VERSION)
IMAGE_TAG_UNIQ=$(IMAGE_TAG)
IMAGE=$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_UNIQ=$(IMAGE_NAME):$(IMAGE_TAG_UNIQ)

ANTHROPIC_API_KEY=$(shell env | grep ANTHROPIC_API_KEY | cut -d'=' --fields 2)
ZULIP_SITE=$(shell cat .env | grep ZULIP_SITE | cut -d'=' -f 2)
ZULIP_EMAIL=$(shell cat .env | grep ZULIP_EMAIL | cut -d'=' -f 2)
ZULIP_API_KEY=$(shell cat .env | grep ZULIP_API_KEY | cut -d'=' -f 2)
GITHUB_MATCHOX_TOKEN=$(shell cat .env | grep GITHUB_MATCHOX_TOKEN | cut -d'=' -f 2)
NAUTOBOT_TOKEN=$(shell cat .env | grep NAUTOBOT_TOKEN | cut -d'=' -f 2)
NAUTOBOT_URL=$(shell cat .env | grep NAUTOBOT_URL | cut -d'=' -f 2)

RUN_ARGS=\
	-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
	-e GITHUB_MATCHBOX_KEY=$(ZULIP_EMAIL) \
	-e GITHUB_MATCHBOX_TOKEN=$(GITHUB_MATCHBOX_TOKEN) \
	-e ZULIP_EMAIL=$(ZULIP_EMAIL) \
	-e ZULIP_API_KEY=$(ZULIP_API_KEY) \
	-e ZULIP_SITE=$(ZULIP_SITE) \
	-e NAUTOBOT_TOKEN=$(NAUTOBOT_TOKEN) \
	-e NAUTOBOT_URL=$(NAUTOBOT_URL) \
	-e RITSUKO_VERSION='$(VERSION) (local development)' \

.PHONY: help
.DEFAULT_GOAL=help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: build
build: ## Build production Docker image
	@echo "Building version: $(VERSION)"
	docker build \
		--progress=plain \
		--build-arg VERSION=$(VERSION) \
		-t $(IMAGE) \
		-t $(IMAGE_UNIQ) \
		.

.PHONY: build-debug
build-debug: ## Build debug Docker image with testing tools
	@echo "Building debug version: $(VERSION)-debug"
	docker build \
		--progress=plain \
		--build-arg VERSION=$(VERSION)-debug \
		-f Dockerfile.debug \
		-t $(IMAGE_NAME):debug-$(UNIQ) \
		.

.PHONY: push
push: build
	docker push \
		$(IMAGE_UNIQ)

.PHONY: run
run: build ## Runs the container locally with docker
	docker run -ti \
		$(RUN_ARGS) \
		docker.io/$(IMAGE_UNIQ)

.PHONY: release
release: ## Updates chart appVersion, commits it
	@echo "Current version: $(VERSION)"
	@echo "Updating chart/Chart.yaml with version $(VERSION)"
	yq -y --in-place ".appVersion = \"$(VERSION)\"" chart/Chart.yaml
	git add chart/Chart.yaml
	git commit -m "chore: update chart appVersion to $(VERSION)"
	@echo "Release committed. To create tag, run: make tag"
	@echo "To push, run: make push-release"

dev: ## Runs the container locally
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		$(RUN_ARGS) \
		$(IMAGE_UNIQ)

debug: build-debug ## Runs the debug container locally with debug tools
	docker run -ti $(RUN_ARGS) \
		-v $(HOME)/.kube:/home/zulip/.kube \
		$(IMAGE_NAME):debug-$(UNIQ)


local:
	. .venv/bin/activate
	./run.sh

test: ## Run unit tests
	@if [ ! -d .venv ]; then \
		echo "Virtual environment not found. Creating it..."; \
		python3 -m venv .venv; \
		.venv/bin/pip install -r src/requirements.txt; \
		.venv/bin/pip install -r src/requirements-test.txt; \
	fi
	.venv/bin/python -m pytest tests/test_bot.py tests/test_fetcher.py -v

test-coverage: ## Run tests with coverage report
	@if [ ! -d .venv ]; then \
		echo "Virtual environment not found. Creating it..."; \
		python3 -m venv .venv; \
		.venv/bin/pip install -r src/requirements.txt; \
		.venv/bin/pip install -r src/requirements-test.txt; \
	fi
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
	@echo $(RUN_ARGS)

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

.PHONY: tag
tag: ## Create and push git tag based on semantic version
	@echo "Current version from git: $(VERSION)"
	@read -p "Enter new version tag (e.g., v1.5.1): " NEW_VERSION; \
	if [ -z "$$NEW_VERSION" ]; then \
		echo "Error: Version cannot be empty"; \
		exit 1; \
	fi; \
	echo "Creating tag $$NEW_VERSION"; \
	git tag -a $$NEW_VERSION -m "Release $$NEW_VERSION"; \
	echo "Tag created. To push, run: git push origin $$NEW_VERSION"

.PHONY: push-release
push-release: ## Push commits and tags to remote
	git push origin $(shell git branch --show-current)
	git push origin --tags

.PHONY: version
version: ## Show current version information
	@echo "Git version: $(GIT_VERSION)"
	@echo "Version: $(VERSION)"
	@echo "Image tag: $(IMAGE_TAG)"
	@echo "Unique tag: $(IMAGE_TAG_UNIQ)"
	@echo "Full image: $(IMAGE_UNIQ)"
