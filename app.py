from flask import Flask, request, jsonify, render_template
from rasa.core.agent import Agent
import sqlite3
import random
import json
import asyncio
import os

app = Flask(__name__)

# Cargar el modelo de Rasa directamente
try:
    print("🔍 Cargando modelo de Rasa desde ./models...")
    agent = Agent.load("./models")
    print("✅ Modelo de Rasa cargado correctamente.")
except FileNotFoundError:
    print("❌ Error: La carpeta 'models/' no existe. Ejecuta primero: python -m rasa train")
    agent = None
except Exception as e:
    print(f"❌ Error al cargar el modelo de Rasa: {e}")
    agent = None

# Función para manejar el texto de forma síncrona
def handle_text_sync(message):
    if not agent:
        return [{"text": "Lo siento, el modelo no está cargado. Ejecuta primero: python -m rasa train"}]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        responses = loop.run_until_complete(agent.handle_text(message))
        return responses
    except Exception as e:
        print(f"❌ Error al procesar el mensaje: {e}")
        return [{"text": "Lo siento, ha ocurrido un error al procesar tu mensaje."}]
    finally:
        loop.close()

# Base de datos de feedback
def init_db():
    conn = sqlite3.connect('data/feedback.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            feedback TEXT NOT NULL,
            correct_answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Cargar contenidos de la plataforma
def load_contenidos_plataforma():
    try:
        with open('data/contenidos_plataforma_laudato_si.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ No se encontró el archivo de contenidos de la plataforma. Usando datos vacíos.")
        return []

contenidos_plataforma = load_contenidos_plataforma()

# Citas de Laudato Si’
citas_laudato_si = [
    "'La Tierra, nuestra casa, parece convertirse cada vez más en un inmenso depósito de porquería.' (LS 21)",
    "'Todo está conectado. Concierne al género humano reconocer el valor de los otros seres vivos.' (LS 42)",
    "'La ecología integral también incluye la justicia social y el cuidado de los pobres.' (LS 49)",
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not agent:
        return jsonify({"response": "Lo siento, el modelo no está cargado. Ejecuta primero: python -m rasa train"})

    data = request.json
    message = data['message']

    responses = handle_text_sync(message)
    bot_response = responses[0]['text'] if responses else "Lo siento, no tengo una respuesta para eso."

    if bot_response.lower() == message.lower():
        bot_response = "Lo siento, no entiendo tu pregunta. ¿Puedes preguntar sobre la Laudato Si’, acciones ecológicas o citas?"

    # Guardar conversación (CORREGIDO: especifica las columnas)
    try:
        conn = sqlite3.connect('data/feedback.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversations (user_message, bot_response, timestamp) VALUES (?, ?, datetime("now"))', (message, bot_response))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ No se pudo guardar la conversación: {e}")

    return jsonify({"response": bot_response})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    message = data['message']
    feedback_type = data['feedback']
    correct_answer = data.get('correct_answer', None)

    # Guardar feedback (CORREGIDO: especifica las columnas)
    try:
        conn = sqlite3.connect('data/feedback.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (message, feedback, correct_answer, timestamp) VALUES (?, ?, ?, datetime("now"))', (message, feedback_type, correct_answer))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"⚠️ Error al guardar feedback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cita_aleatoria', methods=['GET'])
def cita_aleatoria():
    return jsonify({"cita": random.choice(citas_laudato_si)})

@app.route('/api/contenidos', methods=['GET'])
def get_contenidos():
    tipo = request.args.get('tipo', None)
    if tipo:
        contenidos_filtrados = [c for c in contenidos_plataforma if c['tipo'] == tipo]
        return jsonify({"contenidos": contenidos_filtrados})
    return jsonify({"contenidos": contenidos_plataforma})

@app.route('/api/contenido_aleatorio', methods=['GET'])
def get_contenido_aleatorio():
    tipo = request.args.get('tipo', None)
    if tipo:
        contenidos_filtrados = [c for c in contenidos_plataforma if c['tipo'] == tipo]
        if not contenidos_filtrados:
            return jsonify({"error": f"No hay contenidos de tipo '{tipo}'."})
        return jsonify({"contenido": random.choice(contenidos_filtrados)})
    if not contenidos_plataforma:
        return jsonify({"error": "No hay contenidos disponibles."})
    return jsonify({"contenido": random.choice(contenidos_plataforma)})

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask en http://localhost:5000")
    print("💡 Asegúrate de que el modelo de Rasa está entrenado (ejecuta: python -m rasa train)")
    app.run(host='0.0.0.0', port=5000, debug=True)
#    port = int(os.environ.get('PORT', 5000))  # Usa el puerto de Heroku o 5000 por defecto
#    print("🚀 Iniciando servidor Flask en el puerto:", port)
#    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False en producción