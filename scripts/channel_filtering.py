import pandas as pd

# ========== STEP 1: CSV unfolding ================= #
# I choose to store trials in a list, for agile analysis.
REST_EYES_OPEN_DIRS = ["new_data/cuantitative/_001_eeg_rest_eyes_open_trial01_right_hand_fist_20251220.csv", "new_data/cuantitative/_001_eeg_rest_eyes_open_trial02_right_hand_fist_20251220.csv"]
REST_EYES_CLOSED_DIRS = ["new_data/cuantitative/_001_eeg_rest_eyes_closed_trial01_right_hand_fist_20251220.csv", "new_data/cuantitative/_001_eeg_rest_eyes_closed_trial02_right_hand_fist_20251220.csv"]
MOTOR_INTENT_DIRS = ["new_data/cuantitative/_001_eeg_motor_intent_trial01_right_hand_fist_20251220.csv", "new_data/cuantitative/_001_eeg_motor_intent_trial02_right_hand_fist_20251220.csv"]
MOTOR_IMAGERY_DIRS = ["new_data/cuantitative/_001_eeg_motor_imagery_trial01_right_hand_fist_20251220.csv", "new_data/cuantitative/_001_eeg_motor_imagery_trial02_right_hand_fist_20251220.csv"]