
from scripts.variable_handling import CualitativeSurvey
from scripts.eeg_recording import EEGRecorder
import csv
from pathlib import Path
import time


def main():
    my_survey = CualitativeSurvey(filename="prueba_2_vacia", p_id="001")
    my_survey.init_csv()
    responses = my_survey.ask_survey()
    my_survey.save_survey_response(responses)

    print("Survey Cualitativa Finalizada.\n")

    my_eeg = EEGRecorder(duration=10, filename="prueba_2_eeg_reposo_anti_cli", r_id="001")
    
    # Iniciar stream automáticamente
    if my_eeg.start_stream():
        # Si el stream se inició correctamente, grabar
        my_eeg.start_recording()
    else:
        print("No se pudo completar la grabación.")


if __name__ == "__main__":
    main()

