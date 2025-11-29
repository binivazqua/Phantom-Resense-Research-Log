## Basic Survey for EEG Data Analysis ##

import csv 
from pathlib import Path
import time


class CualitativeSurvey:
    def __init__(self, filename, p_id):
        self.date_str = time.strftime("%Y%m%d")  # Fecha consistente para toda la sesión
        self.filename = f"data/cualitative/cual_survey_{filename}_{self.date_str}.csv"
        self.p_id = p_id

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
    def init_csv(self):
        """
            Crea el CSV de recolección de datos cualitativos, si es que ya NO 
            existe.
            Si ya existe, pass.
        """
        file_path = Path(self.filename)
        if not file_path.exists():
            with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.FIELDNAMES)
                writer.writeheader()
        else:
            print(f"Usando archivo existente: {self.filename}")

    def ask_survey(self)-> dict: 
        """
            Realiza la encuesta y devuelve las respuestas 
            en un diccionario. (-> dict)
        """
        print("*******----***** NEW EEG SURVEY *****----*******")
        
        # Preguntas a respuestas individuales con data handling 
        p_id = self.p_id
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

    def save_survey_response(self, response: dict):
        """
            Guarda la respuesta de la encuesta en el CSV.
            Usa DictWriter para escribir el diccionario estilo "lenguaje natural".
        """
        with open(self.filename, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.FIELDNAMES)
            writer.writerow(response)
        # Debug print st.
        print(f"Survey saved at: {self.filename}")









