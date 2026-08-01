#!/usr/bin/env bash
# Script de build para Render. Se ejecuta en cada deploy.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Crea el superusuario inicial si se definieron las variables de entorno
# DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD en Render. Se ignora el error si
# el usuario ya existe (deploys posteriores).
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]]; then
  python manage.py createsuperuser --noinput || true
fi
