from eeg_csv_handler import EEGFileHandling
from eeg_plotting import BrainPlotter
from filtering_handler import DataFilter
from feature_extraction import FeatureExtractor

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

# STEP 2: Example of plotting using BrainPlotter class
reo_plotter = BrainPlotter(reo_data)
rec_plotter = BrainPlotter(rec_data)

# reo_plotter.plotchannel(channel='AF7', seconds=10, title='Rest Eyes Open (RAW)') 
# rec_plotter.plotchannel(channel='AF7', seconds=10, title='Rest Eyes Closed (RAW)')
# plotter.plot_multiple_channels(channels=['TP9', 'AF7', 'AF8', 'TP10'], seconds=10)

# STEP 3: Filter data and plot again
reo_filter = DataFilter(lowcut=1.0, highcut=50.0, fs=256.0, notch_freq=60.0, quality_factor=30.0)
rec_filter = DataFilter(lowcut=1.0, highcut=50.0, fs=256.0, notch_freq=60.0, quality_factor=30.0)

reo_data_filtered = reo_filter.filter_data(reo_data)
rec_data_filtered = rec_filter.filter_data(rec_data)

reo_plotter_filtered = BrainPlotter(reo_data_filtered)
rec_plotter_filtered = BrainPlotter(rec_data_filtered)


# reo_plotter_filtered.plotchannel(channel='AF7', seconds=10, title='Rest Eyes Open - Filtered')
# rec_plotter_filtered.plotchannel(channel='AF7', seconds=10, title='Rest Eyes Closed - Filtered')
# plotter_filtered.plot_multiple_channels(channels=['TP9', 'AF7', 'AF8', 'TP10'], seconds=10)

rest_c1omparison_plot = rec_plotter_filtered.compare_plots(
    rec_data_filtered,
    reo_data_filtered,
    channel='AF7',
    seconds=10,
    plot_type='overlap'
)

rest_comparison_plot = rec_plotter_filtered.compare_plots(
    rec_data_filtered,
    reo_data_filtered,
    channel='AF7',
    seconds=10,
    plot_type='sidetoside'
)

# STEP 4: Extract and compare RMS features
channel = 'AF7'

# Extract RMS features for both conditions
rec_extractor = FeatureExtractor(rec_data_filtered[channel])
reo_extractor = FeatureExtractor(reo_data_filtered[channel])

# Extract features with 1-second windows and 50% overlap
rec_times, rec_rms, rec_mav, rec_energy = rec_extractor.window_feature_extraction(
    df=rec_data_filtered[channel],
    window_duration=1.0,
    overlap=0.5
)

reo_times, reo_rms, reo_mav, reo_energy = reo_extractor.window_feature_extraction(
    df=reo_data_filtered[channel],
    window_duration=1.0,
    overlap=0.5
)


reo_extractor.plot_features(
    time_rest=rec_times,
    time_active=reo_times,
    feature_val_rest=rec_rms,
    feature_val_active=reo_rms,
    feature_name='RMS',
    channel_name=channel
)

print(f"\nRMS Statistics for {channel}:")
print(f"Rest Eyes Closed - Mean: {rec_rms.mean():.2f}, Std: {rec_rms.std():.2f}")
print(f"Rest Eyes Open - Mean: {reo_rms.mean():.2f}, Std: {reo_rms.std():.2f}")