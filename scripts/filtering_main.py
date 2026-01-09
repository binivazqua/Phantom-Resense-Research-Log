from eeg_csv_handler import EEGFileHandling
from eeg_plotting import BrainPlotter
from filtering_handler import DataFilter
from feature_extraction import FeatureExtractor
from frequency_handler import FrequencyHandler

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
mi_data = loader.motor_intent[0]  # First motor intent trial
mim_data = loader.motor_imagery[0]  # First motor imagery trial

print("\nData loaded successfully.")
print(mi_data.head())  # Example: print first few rows of the first rest eyes open trial

# STEP 2: Example of plotting using BrainPlotter clas

mi_plotter = BrainPlotter(mi_data)
mi_plotter.plot_multiple_channels(
    channels=["AF7", "TP9"],
    seconds=10
)

# STEP 3: Filter data

mi_filter = DataFilter(
    lowcut=1.0,
    highcut=50.0,
    notch_freq=60,
    quality_factor=30,
)

# CREATE NEW FILTERED "DATA OBJECT"
mi_data_filtered = mi_filter.filter_data(mi_data)

# Create a plotter for filtered data and work independently

mi_data_filtered_plotter = BrainPlotter(mi_data_filtered) 

mi_data_filtered_plotter.plot_multiple_channels(
    channels=["AF7", "TP9"],
    seconds=10
)

# Step 4: Frequency segmentation
mi_freq_seg = FrequencyHandler()

mi_mu_df = mi_freq_seg.freq_extraction(mi_data_filtered, "mu")
mi_beta_df = mi_freq_seg.freq_extraction(mi_data_filtered, "beta")

# and plot new data.
mi_mu_plotter = BrainPlotter(mi_mu_df)
mi_beta_plotter = BrainPlotter(mi_beta_df)
mi_mu_plotter.plot_multiple_channels(
    channels=["AF7", "TP9"],
    seconds= 10,
    title="Mu Frequency"
)

mi_beta_plotter.plot_multiple_channels(
    channels=["AF7", "TP9"],
    seconds= 10,
    title="Beta Frequency"
)






