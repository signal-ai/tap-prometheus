python_version = 3.10.7
pip_version    = 20.3
image_url      = tap-	prometheus:latest

config = example_config.json

.PHONY: install-tools
install-tools: ## installs tools which are used by other make targets
	./dev/install-tools.sh

.PHONY: install-environment
install-environment:
	pyenv install --skip-existing $(python_version)
	pyenv local $(python_version)
	poetry env use $(python_version) \
		&& poetry run pip install --upgrade pip==$(pip_version) \
		&& poetry run pre-commit install --install-hooks

.PHONY: install-dependencies
install-dependencies: install-environment
	@poetry install

.PHONY: build-docker
build-docker:
	@docker build -t $(image_url) \
		--build-arg PYTHON_VERSION=$(python_version) \
		--build-arg POETRY_VERSION=$(poetry_version) \
		--build-arg OVERRIDE_PIP_VERSION=$(pip_version) \
		--progress=plain \
		.

.PHONY: start-docker
start-docker:
	@docker container run -v $$(pwd):/srv  tap-prometheus:latest poetry run tap-prometheus -c $(config)

.PHONY: start
start:
	poetry run tap-prometheus -c $(config)

.PHONY: test
test:
	poetry run pytest

.PHONY: verify
verify:
	poetry run pre-commit run --all-files
