from flask import Flask, request, jsonify, render_template
from rasa.core.agent import Agent
from rasa.shared.core.events import UserUttered
import sqlite3
import os
import random

app = Flask(__name__)

# Cargar el modelo de Rasa
agent = Agent.load_model("./models")

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

# Citas de Laudato Si’ para respuestas aleatorias
citas_laudato_si = [
    "'La Tierra, nuestra casa, parece convertirse cada vez más en un inmenso depósito de porquería.' (LS 21)",
    "'Todo está conectado. Concierne al género humano reconocer el valor de los otros seres vivos.' (LS 42)",
    "'La ecología integral también incluye la justicia social y el cuidado de los pobres.' (LS 49)",
    "'Se requiere una conversión ecológica, que implique cambios profundos en nuestros estilos de vida.' (LS 216)",
    "'El destino de la Tierra también es nuestro destino.' (LS 163)"
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data['message']

    # Guardar conversación
    conn = sqlite3.connect('data/feedback.db')
    cursor = conn.cursor()

    # Procesar con Rasa
    responses = agent.handle_text(message)
    bot_response = responses[0]['text']

    # Guardar en la base de datos
    cursor.execute('INSERT INTO conversations VALUES (?, ?, datetime("now"))', (message, bot_response))
    conn.commit()
    conn.close()

    return jsonify({"response": bot_response})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    message = data['message']
    feedback_type = data['feedback']
    correct_answer = data.get('correct_answer', None)

    # Guardar feedback
    conn = sqlite3.connect('data/feedback.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback VALUES (?, ?, ?, datetime("now"))', (message, feedback_type, correct_answer))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route('/api/cita_aleatoria', methods=['GET'])
def cita_aleatoria():
    return jsonify({"cita": random.choice(citas_laudato_si)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)