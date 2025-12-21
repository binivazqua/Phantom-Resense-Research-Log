from eeg_csv_handler import EEGFileHandling

# STEP 1: Define data paths

REST_EYES_OPEN_DIRS = [
    "new_data/cuantitative/_001_eeg_rest_eyes_open_trial01_right_hand_fist_20251220.csv",
    "new_data/cuantitative/_001_eeg_rest_eyes_open_trial02_right_hand_fist_20251220.csv"
]

REST_EYES_CLOSED_DIRS = [
    "new_data/cuantitative/_001_eeg_rest_eyes_closed_trial01_right_hand_fist_20251220.csv",
    "new_data/cuantitative/_001_eeg_rest_eyes_closed_trial02_right_hand_fist_20251220.csv"
]

MOTOR_INTENT_DIRS = [
    "new_data/cuantitative/_001_eeg_motor_intent_trial01_right_hand_fist_20251220.csv",
    "new_data/cuantitative/_001_eeg_motor_intent_trial02_right_hand_fist_20251220.csv"
]

MOTOR_IMAGERY_DIRS = [
    "new_data/cuantitative/_001_eeg_motor_imagery_trial01_right_hand_fist_20251220.csv",
    "new_data/cuantitative/_001_eeg_motor_imagery_trial02_right_hand_fist_20251220.csv"
]

# Load data using the class
loader = EEGFileHandling()
loader.load_all_data(
    REST_EYES_OPEN_DIRS,
    REST_EYES_CLOSED_DIRS,
    MOTOR_INTENT_DIRS,
    MOTOR_IMAGERY_DIRS
)

# STEP 1.1: Access loaded data correctly.
reo_data = loader.rest_eyes_open[0]  # First rest eyes open trial
rec_data = loader.rest_eyes_closed[0]  # First rest eyes closed trial
mi_data = loader.motor_intent[0]  # First motor intent trial
mim_data = loader.motor_imagery[0]  # First motor imagery trial

print("\nData loaded successfully.")
print(reo_data.head())  # Example: print first few rows of the first rest eyes open trial