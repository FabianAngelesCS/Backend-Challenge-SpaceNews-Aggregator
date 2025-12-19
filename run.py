#!/usr/bin/env python
"""Script de conveniencia para ejecutar el servidor en puerto 8500"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from django.core.management import execute_from_command_line
    
    # Ejecutar runserver en puerto 8500 por defecto
    sys.argv = ['manage.py', 'runserver', '8500']
    execute_from_command_line(sys.argv)
