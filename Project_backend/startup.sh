#!/bin/sh
python3 -m venv pb
source pb/bin/activate
pip install django==4.1.2
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install --upgrade djangorestframework-simplejwt
pip install Pillow
pip install "django-phonenumber-field[phonenumberslite]"
pip install django-multiselectfield
pip install django-credit-cards
pip install python-dateutil
pip install django-taggit
# Installs phonenumbers extended features (e.g. geocoding)
pip install "django-phonenumber-field[phonenumbers]"
# Installs datetime field
pip install python-dateutil
pip install django-cors-headers
python3 manage.py makemigrations
python3 manage.py migrate

export DJANGO_SUPERUSER_PASSWORD=admin
python3 manage.py createsuperuser --no-input --email admin@test.com --username admin
