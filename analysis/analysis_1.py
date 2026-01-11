import sys
from pathlib import Path

# Add parent directory to path to import from scripts
sys.path.append(str(Path(__file__).parent.parent))

from scripts.eeg_csv_handler import EEGFileHandling
from scripts.eeg_plotting import BrainPlotter
from scripts.filtering_handler import DataFilter
from scripts.feature_extraction import FeatureExtractor
from scripts.frequency_handler import FrequencyHandler

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
mi_data = loader.motor_imagery[0]  # First motor intent trial
rest_data = loader.rest_eyes_closed[0]  # First rest eyes closed trial


print("\nData loaded successfully.")

# STEP 2: Example of plotting using BrainPlotter clas

mi_plotter = BrainPlotter(mi_data)
mi_plotter.plot_multiple_channels(
    title="Motor Imagery Data Raw",
    channels=["AF7", "TP9"],
    seconds=10
)

rest_plotter = BrainPlotter(rest_data)
rest_plotter.plot_multiple_channels(
    title="Rest Data Raw",
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

rest_filter = DataFilter(
    lowcut=1.0,
    highcut=50.0,
    notch_freq=60,
    quality_factor=30,
)


# CREATE NEW FILTERED "DATA OBJECT"
mi_data_filtered = mi_filter.filter_data(mi_data)
rest_data_filtered = rest_filter.filter_data(rest_data)

# Create a plotter for filtered data and work independently

mi_data_filtered_plotter = BrainPlotter(mi_data_filtered) 
rest_data_filtered_plotter = BrainPlotter(rest_data_filtered)

mi_data_filtered_plotter.plot_multiple_channels(
    title="Filtered Motor Imagery Data",
    channels=["AF7", "TP9"],
    seconds=10
)

rest_data_filtered_plotter.plot_multiple_channels(
    title="Filtered Rest Eyes Closed Data",
    channels=["AF7", "TP9"],
    seconds=10
)

mi_plotter.compare_plots(
    rest_data_filtered, 
    mi_data_filtered, 
    channel="AF7", 
    seconds=10, 
    plot_type="sidetoside",
    title="Rest vs Motor Imagery"
)
mi_plotter.compare_plots(
    rest_data_filtered, 
    mi_data_filtered, 
    channel="TP9",
    seconds=10,
    plot_type="sidetoside",
    title="Rest vs Motor Imagery"
)

# # Step 4: Frequency segmentation

# MOTOR IMAGERY DATA
mi_freq_seg = FrequencyHandler()

# use freq extraction to get mu and beta bands
mi_mu_df = mi_freq_seg.freq_extraction(mi_data_filtered, "mu")
mi_beta_df = mi_freq_seg.freq_extraction(mi_data_filtered, "beta")

# and plot new data.
mi_mu_plotter = BrainPlotter(mi_mu_df)
mi_beta_plotter = BrainPlotter(mi_beta_df)
# mi_mu_plotter.plot_multiple_channels(
#     channels=["AF7", "TP9"],
#     seconds= 10,
#     title="Motor Imagery in Mu Frequency"
# )

# mi_beta_plotter.plot_multiple_channels(
#     channels=["AF7", "TP9"],
#     seconds= 10,
#     title="Motor Imagery in Beta Frequency"
# )

# REST DATA
rest_freq_seg = FrequencyHandler()

rest_mu_df = rest_freq_seg.freq_extraction(rest_data_filtered, "mu")
rest_beta_df = rest_freq_seg.freq_extraction(rest_data_filtered, "beta")

# plotters

rest_mu_plotter = BrainPlotter(rest_mu_df)
rest_beta_plotter = BrainPlotter(rest_beta_df)

# plot 

# rest_mu_plotter.plot_multiple_channels(
#     channels=["AF7", "TP9"],
#     seconds=10,
#     title="Rest in Mu Frequency"
# )

# rest_beta_plotter.plot_multiple_channels(
#     channels=["AF7", "TP9"],
#     seconds=10,
#     title="Rest in Beta Frequency"
# )

# COMPARISON
mi_mu_plotter.compare_plots(
    rest_mu_df,
    mi_mu_df,
    df_1_alias="Rest Mu",
    df_2_alias="MI Mu",
    channel="AF7",
    seconds=10,
    plot_type="overlap",
    title="Rest vs Motor Imagery in Mu Band AF7 channel"
)

mi_beta_plotter.compare_plots(
    rest_beta_df,
    mi_beta_df,
    df_1_alias="Rest Beta",
    df_2_alias="MI Beta",
    channel="AF7",
    seconds=10,
    plot_type="overlap",
    title="Rest vs Motor Imagery in Beta Band AF7 channel"
)


mi_mu_plotter.compare_plots(
    rest_mu_df,
    mi_mu_df,
    df_1_alias="Rest Mu",
    df_2_alias="MI Mu",
    channel="TP9",
    seconds=10,
    plot_type="overlap",
    title="Rest vs Motor Imagery in Mu Band TP9 channel"
)

mi_beta_plotter.compare_plots(
    rest_beta_df,
    mi_beta_df,
    df_1_alias="Rest Beta",
    df_2_alias="MI Beta",
    channel="TP9",
    seconds=10,
    plot_type="overlap",
    title="Rest vs Motor Imagery in Beta Band TP9 channel"
)