VERSION_TAG=$(shell git rev-parse --short HEAD)

##A quality of life tool for teams.
##Usage:	make [command]...
##
##Commands:

.DEFAULT_GOAL := help

init: ## Initialize environment
	# - Install your dependencies via gem, maven, etc.
	# - Download sql dumps or copy configuration templates
	#   that a dev needs to get up and running.
	# - Install git hooks (more below)
	"$(MAKE)" --quiet hook

hook: ## Install git hooks
	git config core.hooksPath .githooks

unhook: ## Uninstall git hooks
	git config core.hooksPath ''

test: ## Run tests
	# Run unit tests, code coverage, and linters
	# Remove all cached pyc files, they don't play nice with the containers
	find . -name "*.pyc" -delete
	# Build the docker image
	docker build -f Dockerfile.test -t test-image .
	# Run `tox` on the image
	docker run --rm -t test-image tox

build: ## Build docker image
	# Build Dockerfile
	docker build -f Dockerfile -t service-image:$(VERSION_TAG) .

run: build ## Build & run docker image

push: build ## Build & push Docker images to registry
	# Push Docker images

docs: ## Generate documentation
	# Generate your API documentation (you do have some, don't you?)

package: ## Prepare artifacts to be shipped
	# Build a release tarball or jar or executable

dev: ## Start development environment
	# Start up a development server or process e.g. `vagrant up` or `node server.js`
	# Bonus: open that page in the user's browser automatically
	vagrant up
	vagrant ssh

install: ## Install project
	# If your project builds an executable, place it in the `$PATH`.
	# E.g. copy or symlink it into `/usr/local/bin`

deploy: ## Deploy project
	# If you have a simple deployment mechanism, like `rsync` or `s3cmd`, let
	# the Makefile take care of it.

.PHONY: test docs

help: ## Display this help text
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}{printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'

##
##Maintained by <maintainer@email.address>