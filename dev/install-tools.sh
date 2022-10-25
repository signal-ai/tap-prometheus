#!/usr/bin/env bash

project_root="$(git rev-parse --show-toplevel)"

# several checks for whether we're using ZSH as ZSH_VERSION didn't seem reliable
if [ -n "$ZSH_VERSION" ] || [ "$ZSH_NAME" = "zsh" ] || [ -f "$HOME/.zshrc" ]; then
  touch ~/.zprofile
else
  touch ~/.bash_profile
fi

echo "Installing pyenv"
if [[ "$OSTYPE" == "darwin"* ]]; then

  if [[ $(command -v brew) == "" ]]; then
    echo "Homebrew is not installed, please install it by following instructions at https://brew.sh/ "
    exit 1
  fi

  brew update
  brew install \
    pyenv
else
  curl https://pyenv.run | bash
fi

if [[ -n "$(command -v apt-get)" ]]; then
  echo "Detected apt-get, installing required packages for python setup"
  sudo apt-get update -y
  sudo apt-get install -y \
    libffi-dev \
    libtool \
    libsasl2-dev \
    build-essential \
    sqlite3 \
    libsqlite3-dev
fi

echo "Installing poetry"
curl -sSL https://install.python-poetry.org | python3 -
echo "poetry successfully installed. You should ensure that ~/.poetry/bin is available on your PATH"

set -e
