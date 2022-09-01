ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION-slim-buster

# set poetry version, used by the get-poetry.py installer
ARG POETRY_VERSION
ENV POETRY_VERSION=$POETRY_VERSION
ENV POETRY_VIRTUALENVS_CREATE=false

# prefix with OVERRIDE_ to prevent base image ENV var being used
ARG OVERRIDE_PIP_VERSION
ENV PIP_VERSION=$OVERRIDE_PIP_VERSION

WORKDIR /srv

RUN apt-get update -yqq && \
  apt-get install -yqq --no-install-recommends \
  curl build-essential git \
  && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" \
  && rm -rf ~/.cache

ENV PATH="$PATH:/root/.local/bin"

COPY ./pyproject.toml ./poetry.lock /

RUN poetry run pip install --no-cache-dir --upgrade pip==${PIP_VERSION} \
  && poetry install --no-dev \
  && rm -rf ~/.cache
