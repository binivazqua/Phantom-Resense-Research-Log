## Basic Survey for EEG Data Analysis ##

import csv 
from pathlib import Path
import time


class CualitativeSurvey:
    def __init__(self, filename, p_id):
        self.date_str = time.strftime("%Y%m%d")  # Fecha consistente para toda la sesión
        self.filename = f"new_data/cualitative/cual_survey_{filename}_{self.date_str}.csv"
        self.p_id = p_id

    # 2. Define los headers.
    FIELDNAMES = [
        "P_ID",
        "Gender",
        "Stress_Level",
        "Sleep_Quality",
        "Most_Recent_Meal",
        "Amount_of_Caffeine",
        "Initial_Notes",
        "Ending_Notes",
        "Overall_Focus_Level",
        "Motor_Imagery_Intensity",

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

    def ask_initial_survey(self)-> dict: 
        """
            Realiza la encuesta inicial (previa a la sasión) y devuelve las respuestas 
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
            "Initial_Notes": notes,
        }

        return row;
    
    def ask_final_survey(self) -> dict:
        """
            Realiza la encuesta final (post sesión) y devuelve las respuestas 
            en un diccionario. (-> dict)
        """
        print("*******----***** FINAL EEG SURVEY *****----*******")
        
        # Preguntas a respuestas individuales con data handling 
        overall_focus_level = int(input("Nivel general de concentración durante la sesión (1-5): "))
        motor_imagery_intensity = int(input("Intensidad de la imaginación motora (1-5): "))
        ending_notes = input("Notas adicionales al finalizar la sesión (opcional): ").lower().strip()

        # Crear la row del dict:
        row = {
            "P_ID": self.p_id,
            "Overall_Focus_Level": overall_focus_level,
            "Motor_Imagery_Intensity": motor_imagery_intensity,
            "Ending_Notes": ending_notes,
        }

        return row;

    def save_survey_response(self, initial_response: dict, final_response: dict = None):
        """
            Guarda la respuesta de la encuesta en el CSV.
            Usa DictWriter para escribir el diccionario estilo "lenguaje natural".
        """
        with open(self.filename, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.FIELDNAMES)
            if final_response:
                total_response = {**initial_response, **final_response}
            else:
                total_response = initial_response
            writer.writerow(total_response)
        # Debug print st.
        print(f"Survey saved at: {self.filename}")









