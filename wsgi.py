import sys
import os

# Agrega el directorio de tu aplicación al path de Python
path = '/home/Amaia/Taller_Despliege_Directo/'
if path not in sys.path:
    sys.path.append(path)

# Importa tu aplicación Flask
from app import app as application

# PythonAnywhere busca la variable 'application' por defecto
if __name__ == '__main__':
    application.run() 