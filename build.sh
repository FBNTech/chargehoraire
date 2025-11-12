#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies with binary wheels only (no compilation)
pip install --only-binary=:all: -r requirements.txt || pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
