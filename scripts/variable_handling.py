## Basic Survey for EEG Data Analysis ##

import csv 
from pathlib import Path
import time

CSV_FILE_PATH = Path("data/cualitative/eeg_survey_data.csv")

# 2. Define los headers.
FIELDNAMES = [
    "P_ID",
    "Gender",
    "Stress_Level",
    "Sleep_Quality",
    "Most_Recent_Meal",
    "Amount_of_Caffeine",
    "Notes"
]

# 3. Inicializar el CSV
def init_csv(file_path: Path):
    """
        Crea el CSV de recolección de datos cualitativos, si es que ya NO 
        existe.
        Si ya existe, pass.
    """
    if not file_path.exists():
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
    else:
        print(f"Usando archivo existente: {file_path}")

def ask_survey()-> dict: 
    """
        Realiza la encuesta y devuelve las respuestas 
        en un diccionario. (-> dict)
    """
    print("*******----***** NEW EEG SURVEY *****----*******")
    
    # Preguntas a respuestas individuales con data handling 
    p_id = input("Participant ID (P_ID): ")
    gender = input("Genero: ")
    stress_level = int(input("Nivel de Estrés (1-5): "))
    sleep_quality = input("Calidad del Sueño (Buena/Regular/Mala): ").lower().strip()
    most_recent_meal = input("Aporte energético de la última comida (Alto/Medio/Bajo): ").lower().strip()
    amount_of_caffeine = input("Cantidad de cafeína consumida hoy (Ninguna/Poca/Mucha): ").lower().strip()
    notes = input("Notas adicionales (opcional): ").lower().strip()

    # Crear la row del dict:
    row = {
        "P_ID": p_id,
        "Gender": gender,
        "Stress_Level": stress_level,
        "Sleep_Quality": sleep_quality,
        "Most_Recent_Meal": most_recent_meal,
        "Amount_of_Caffeine": amount_of_caffeine,
        "Notes": notes,
    }

    return row;

def save_survey_response(file_path: Path, response: dict):
    """
        Guarda la respuesta de la encuesta en el CSV.
        Usa DictWriter para escribir el diccionario estilo "lenguaje natural".
    """
    with open(file_path, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writerow(response)
    # Debug print st.
    print(f"Recording successfully saved at: {file_path}")

def generate_file_path(base_path: Path, participant_id: str) -> Path:
    """
        Genera un path de archivo basado en la fecha y el ID del participante.
        Ejemplo: "data/eeg_data_participant_123.csv"
    """
    date = time.strftime("%Y%m%d")
    filename = f"eeg_data_pid_{participant_id}_{date}.csv"
    return base_path / filename


# Crear un main para ejecutar 
def main():
    # Realizar la encuesta
    response = ask_survey()
    
    # Generar el path dinámico usando el P_ID
    base_path = Path("data/cualitative")
    base_path.mkdir(parents=True, exist_ok=True)  # Crear el directorio si no existe
    
    file_path = generate_file_path(base_path, response["P_ID"])
    
    # Inicializar el CSV si no existe
    init_csv(file_path)

    # Guardar la respuesta en el CSV
    save_survey_response(file_path, response)

main()




