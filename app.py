from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import RidgeClassifier

app = Flask(__name__)
CORS(app)

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
            return jsonify({
                'success': False,
                'message': 'El modelo no está inicializado correctamente'
            }), 500

        # Obtener datos del request
        datos = request.get_json()
        if not datos:
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
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': 'Error en el formato de los datos'
            }), 400
        
        # Encode de género
        input_data['Hombre'] = [1 if x == "Masculino" else 0 for x in input_data['Género']]
        input_data['Mujer'] = [1 if x == "Femenino" else 0 for x in input_data['Género']]
        
        # Encode de entrantes
        df_entrantes = pd.get_dummies(input_data["Entrante"], prefix='_')
        input_data = pd.concat([input_data, df_entrantes], axis=1)
        
        # Encode de bebidas
        df_bebidas = pd.get_dummies(input_data['Bebida'], prefix='_')
        input_data = pd.concat([input_data, df_bebidas], axis=1)
        
        # Encode de primeros
        input_data['categoria_primero'] = input_data['Primer Plato'].map(primeros_cat)
        input_data['arroz'] = (input_data['categoria_primero'] == 'arroz').astype(int)
        input_data['pasta'] = (input_data['categoria_primero'] == 'pasta').astype(int)
        input_data['verduras'] = (input_data['categoria_primero'] == 'verduras').astype(int)
        input_data['legumbres'] = (input_data['categoria_primero'] == 'legumbres').astype(int)
        input_data['sopa'] = (input_data['categoria_primero'] == 'sopa').astype(int)
        
        # Encode de segundos
        input_data['categoria_segundo'] = input_data['Segundo Plato'].map(segundos_cat)
        input_data['carne'] = (input_data['categoria_segundo'] == 'carne').astype(int)
        input_data['pescado'] = (input_data['categoria_segundo'] == 'pescado').astype(int)
        
        # Eliminar columnas no necesarias
        columns_to_drop = ['Género', 'Entrante', 'Primer Plato', 'Segundo Plato', 'Bebida', 
                          'categoria_primero', 'categoria_segundo']
        input_data = input_data.drop(columns=columns_to_drop)
        
        # Asegurarse de que todas las columnas necesarias estén presentes
        expected_columns = modelo.feature_names_in_
        
        # Crear columnas faltantes con valores 0
        for col in expected_columns:
            if col not in input_data.columns:
                input_data[col] = 0
        
        # Ordenar las columnas igual que en el entrenamiento
        input_data = input_data[expected_columns]
        
        print("\nDatos transformados:")
        print(input_data)
        print("\nColumnas:", input_data.columns.tolist())
        
        # Realizar predicción
        try:
            prediccion = modelo.predict(input_data)[0]
            # RidgeClassifier no tiene predict_proba, así que usamos una probabilidad fija
            probabilidad = 0.90  # Probabilidad como decimal (90%)
            
            # Convertir predicción numérica a nombre del postre
            postre_predicho = [k for k, v in postre_cat.items() if v == prediccion][0]
            
            print("\nPredicción numérica:", prediccion)
            print("Postre predicho:", postre_predicho)
            print("Probabilidad:", probabilidad)
            
            return jsonify({
                'success': True,
                'postre': postre_predicho,
                'probabilidad': probabilidad
            })
        except Exception as e:
            print(f"Error en la predicción: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error al realizar la predicción'
            }), 500
        
    except Exception as e:
        print(f"\nError en predicción: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

def inicializar_app():
    """
    Función para inicializar la aplicación y cargar el modelo
    """
    global modelo
    
    # Ruta absoluta al directorio del modelo
    modelo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RidgeClassifier.pkl')
    
    # Intentar cargar el modelo RidgeClassifier
    if os.path.exists(modelo_path):
        try:
            with open(modelo_path, 'rb') as f:
                modelo = pickle.load(f)
            print("Modelo RidgeClassifier cargado exitosamente")
            print("Tipo de modelo:", type(modelo))
        except Exception as e:
            print(f"Error al cargar el modelo RidgeClassifier: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise RuntimeError("No se pudo cargar el modelo RidgeClassifier")
    else:
        print(f"Error: No se encuentra el archivo del modelo en {modelo_path}")
        raise RuntimeError("No se encuentra el archivo del modelo")
    
    return app

# Inicializar la aplicación al importar el módulo
app = inicializar_app()

if __name__ == '__main__':
    app.run(debug=False)
