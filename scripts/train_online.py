from rasa.train import train
import sqlite3
import yaml

def load_feedback_data():
    conn = sqlite3.connect('data/feedback.db')
    cursor = conn.cursor()
    cursor.execute('SELECT message, correct_answer FROM feedback WHERE feedback = "incorrect"')
    feedback_data = cursor.fetchall()
    conn.close()
    return feedback_data

def update_nlu_file(new_examples):
    with open('data/nlu.yml', 'a') as f:
        for message, correct_answer in new_examples:
            f.write(f"\n- intent: preguntar_otro\n  examples: |\n    - {message}\n")

def main():
    # Cargar datos de feedback
    feedback_data = load_feedback_data()
    if not feedback_data:
        print("No hay nuevos datos de feedback para reentrenar.")
        return

    # Actualizar nlu.yml con nuevas preguntas
    update_nlu_file(feedback_data)

    # Reentrenar el modelo
    print("Reentrenando el modelo con nuevos datos...")
    train(
        domain="data/domain.yml",
        config="config.yml",
        training_files="data",
        output="models/laudato_bot_updated",
        online_learning=True
    )
    print("Modelo reentrenado y guardado en models/laudato_bot_updated")

if __name__ == "__main__":
    main()