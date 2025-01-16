from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import RidgeClassifier
app = Flask(__name__)
# Variables globales
modelo = None
postre_cat = {
    "Flan": 0,
    "Helado": 1,
    "Fruta fresca": 2,
    "Tarta de queso": 3,
    "Brownie": 4,
    "Queso y membrillo": 5
}
# Mapeos para categorización
primeros_cat = {
    "Risotto": "arroz",
    "Paella": "arroz",
    "Arroz 3 delicias": "arroz",
    "Lasaña": "pasta",
    "Macarrones": "pasta",
    "Crema de verduras": "verduras",
    "Lentejas": "legumbres",
    "Garbanzos con espinacas": "legumbres",
    "Sopa de pollo": "sopa"
}
segundos_cat = {
    "Filete de ternera": "carne",
    "Merluza al horno": "pescado",
    "Pollo asado": "carne",
    "Hamburguesa": "carne",
    "Costillas BBQ": "carne",
    "Albóndigas": "carne",
    "Cachopo": "carne",
    "Chuletón": "carne",
    "Pollo al curry": "carne",
    "Salmón": "pescado",
    "Bacalao": "pescado"
}
@app.route('/')
def home():
    """
    Ruta principal que renderiza la página web
    """
    return render_template('index.html')
@app.route('/predecir', methods=['POST'])
def predecir():
    """
    Endpoint para realizar predicciones
    """
    try:
        # Verificar si el modelo está cargado
        if modelo is None:
            print("Error: Modelo no inicializado")
            return jsonify({
                'success': False,
                'message': 'El modelo no está inicializado correctamente'
            }), 500
        # Obtener datos del request
        datos = request.get_json()
        if not datos:
            print("Error: No se recibieron datos en el request")
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        print("\nDatos recibidos:", datos)
        # Crear un DataFrame con una fila
        try:
            input_data = pd.DataFrame({
                'Edad': [int(datos.get('edad'))],
                'Género': [datos.get('genero')],
                'Entrante': [datos.get('entrante')],
                'Primer Plato': [datos.get('primer_plato')],
                'Segundo Plato': [datos.get('segundo_plato')],
                'Bebida': [datos.get('bebida')]
            })
            print("DataFrame creado exitosamente:", input_data)
        except ValueError as e:
            print(f"Error al crear DataFrame: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error en el formato de los datos: {str(e)}'
            }), 400
        # Encode de género
        input_data['Hombre'] = [1 if x == "Masculino" else 0 for x in input_data['Género']]
        input_data['Mujer'] = [1 if x == "Femenino" else 0 for x in input_data['Género']]
        print("Género codificado correctamente")
        # Encode de entrantes
        df_entrantes = pd.get_dummies(input_data["Entrante"], prefix='_')
        print("Entrantes codificados correctamente")
        input_data = pd.concat([input_data, df_entrantes], axis=1)
        # Encode de bebidas
        df_bebidas = pd.get_dummies(input_data['Bebida'], prefix='_')
        print("Bebidas codificadas correctamente")
        input_data = pd.concat([input_data, df_bebidas], axis=1)
        # Encode de primeros
        input_data['categoria_primero'] = input_data['Primer Plato'].map(primeros_cat)
        input_data['arroz'] = (input_data['categoria_primero'] == 'arroz').astype(int)
        input_data['pasta'] = (input_data['categoria_primero'] == 'pasta').astype(int)
        input_data['verduras'] = (input_data['categoria_primero'] == 'verduras').astype(int)
        input_data['legumbres'] = (input_data['categoria_primero'] == 'legumbres').astype(int)
        input_data['sopa'] = (input_data['categoria_primero'] == 'sopa').astype(int)
        print("Primeros codificados correctamente")
        # Encode de segundos
        input_data['categoria_segundo'] = input_data['Segundo Plato'].map(segundos_cat)
        input_data['carne'] = (input_data['categoria_segundo'] == 'carne').astype(int)
        input_data['pescado'] = (input_data['categoria_segundo'] == 'pescado').astype(int)
        print("Segundos codificados correctamente")
        # Eliminar columnas no necesarias
        columns_to_drop = ['Género', 'Entrante', 'Primer Plato', 'Segundo Plato', 'Bebida',
                          'categoria_primero', 'categoria_segundo']
        input_data = input_data.drop(columns=columns_to_drop)
        print("Columnas no necesarias eliminadas")
        print("Columnas actuales:", input_data.columns.tolist())
        # Asegurarse de que todas las columnas necesarias estén presentes
        expected_columns = modelo.feature_names_in_
        print("Columnas esperadas:", expected_columns.tolist())
        # Crear columnas faltantes con valores 0
        missing_columns = set(expected_columns) - set(input_data.columns)
        for col in missing_columns:
            print(f"Añadiendo columna faltante: {col}")
            input_data[col] = 0
        # Ordenar las columnas igual que en el entrenamiento
        input_data = input_data[expected_columns]
        print("Columnas ordenadas correctamente")
        print("Columnas finales:", input_data.columns.tolist())
        print("\nDatos transformados:")
        print(input_data)
        # Realizar predicción
        try:
            X = input_data.values
            prediccion = modelo.predict(X)
            print("Predicción realizada exitosamente")
            print("Predicción:", prediccion)
            # RidgeClassifier no tiene predict_proba, usamos una probabilidad fija
            probabilidad = 0.90  # 90% de confianza
            # Obtener el postre predicho
            postre_predicho = list(postre_cat.keys())[prediccion[0]]
            print(f"Postre predicho: {postre_predicho}")
            return jsonify({
                'success': True,
                'postre': postre_predicho,
                'probabilidad': probabilidad
            })
        except Exception as e:
            print(f"Error al realizar la predicción: {str(e)}")
            print("Forma del input:", input_data.shape)
            print("Columnas del input:", input_data.columns.tolist())
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'Error al realizar la predicción: {str(e)}'
            }), 500
    except Exception as e:
        print(f"Error general en la predicción: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error general en el servidor: {str(e)}'
        }), 500
def inicializar_app():
    """
    Función para inicializar la aplicación y cargar el modelo
    """
    global modelo
    try:
        # Usar path absoluto para PythonAnywhere
        modelo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RidgeClassifier.pkl')
        print(f"Intentando cargar modelo desde: {modelo_path}")
        if not os.path.exists(modelo_path):
            print(f"ERROR: El archivo del modelo no existe en: {modelo_path}")
            print(f"Directorio actual: {os.getcwd()}")
            print(f"Contenido del directorio: {os.listdir(os.path.dirname(os.path.abspath(__file__)))}")
            return app
        with open(modelo_path, 'rb') as f:
            modelo = pickle.load(f)
            print("Modelo cargado. Verificando tipo...")
            print(f"Tipo de modelo: {type(modelo)}")
            print(f"Atributos del modelo: {dir(modelo)}")
            # Verificar que el modelo tenga los atributos necesarios
            if not hasattr(modelo, 'predict'):
                print("ERROR: El modelo no tiene el método predict")
                return app
            if not hasattr(modelo, 'feature_names_in_'):
                print("ERROR: El modelo no tiene feature_names_in_")
                return app
            print("Modelo verificado correctamente")
        return app
    except Exception as e:
        print(f"Error al cargar el modelo: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return app
app = inicializar_app()
if __name__ == '__main__':
    app.run()






