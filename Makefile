IMAGE_NAME=asajaroff/ritsuko
IMAGE_TAG=v1.0.0
IMAGE="$(IMAGE_NAME):$(IMAGE_TAG)"
ANTHROPIC_API_KEY=$(shell env | grep ANTHROPIC_API_KEY | cut -d'=' --fields 2)

.PHONY: build
build:
	docker build \
		--progress=plain \
		-t $(IMAGE) \
		. 

.PHONY: push
push: build
	docker push \
		docker.io/$(IMAGE)

.PHONY: run
run: build
	docker run -ti \
		docker.io/$(IMAGE)

dev: ## Mounts the kubernetes config file
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		-e LOG_LEVEL=DEBUG \
		$(IMAGE)

dev-fixed:
	docker run -ti \
		-v $(HOME)/.kube:/home/zulip/.kube \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		$(IMAGE)

local:
	cd src && python bot.py

echo-env:
	echo $(IMAGE)
	echo $(ANTHROPIC_API_KEY)
