
python_version  = 3.7.10
pip_version     = 21.1.1
poetry_version  = 1.1.13

image_url       = singer-tap-prometheus:latest

# DEV SETUP (PYTHON SPECIFIC)
.PHONY: install-tools
install-tools: ## installs tools which are used by other make targets
	@POETRY_VERSION=$(poetry_version) ./dev/install-tools.sh


.PHONY: install-environment
install-environment:
	pyenv install --skip-existing $(python_version)
	pyenv local $(python_version)
# set SYSTEM_VERSION_COMPAT=1 to fix scipy install on big sur
# https://github.com/scipy/scipy/issues/13102
# Note: 'poetry env use' should not be necessary if pyenv is setup correctly but it acts as a fallback if it is not
	export SYSTEM_VERSION_COMPAT=1 \
		&& poetry env use $(python_version) \
		&& poetry run pip install --upgrade pip==$(pip_version) \

.PHONY: install-dependencies
install-dependencies: install-environment
	@poetry install

# BUILD AND PUBLISH
.PHONY: build-image
build-image:
	@docker build -t $(image_url) \
		--build-arg PYTHON_VERSION=$(python_version) \
		--build-arg POETRY_VERSION=$(poetry_version) \
		--build-arg OVERRIDE_PIP_VERSION=$(pip_version) \
		--progress=plain \
		.

.PHONY: run-image
run-image:
	@docker container run -v $$(pwd):/srv/singer-tap -it --entrypoint=/bin/bash singer-tap-prometheus:latest