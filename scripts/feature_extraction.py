import numpy as np

class FeatureExtractor:
    def __init__(self, dataframe):
        self.df = dataframe 
        self.sampling_rate = 256  # Muse 2 default
    

    def normalize_data(self, rest_dataframe, motor_dataframe):
        """
        Normalize motor data based on rest data statistics.
        
        Args:
            rest_dataframe: DataFrame containing rest EEG data
            motor_dataframe: DataFrame containing motor EEG data
            
        Returns:
            normalized_motor_dataframe: DataFrame with normalized motor EEG data
        """
        rest_df_tonorm = rest_dataframe.copy()
        motor_df_tonorm = motor_dataframe.copy()

        for column in motor_dataframe.columns:
            rest_mean = rest_df_tonorm[column].mean()
            rest_std = motor_df_tonorm[column].std()
            z_rest = (rest_df_tonorm[column] - rest_mean) / rest_std
            z_motor = (motor_df_tonorm[column] - rest_mean) / rest_std
            motor_df_tonorm[column] = z_motor
            normalized_motor_dataframe = motor_df_tonorm
            rest_df_tonorm[column] = z_rest
            normalized_rest_dataframe = rest_df_tonorm
        return normalized_rest_dataframe, normalized_motor_dataframe


    def window_feature_extraction(self, df, window_duration, overlap):
        """
        Extracts a 1D EEG signal array in temporal sub windows (which can overlap) 
        and computes features for each window: RMS, MAV, TOTAL ENERGY.

        EEG Signals are mathematically considered as non-stationary signals; 
        however, this function assumes quasi-stationarity within short time windows.

        Each window is interpreted as a local fragment of the signal where 
        statistical properties are constant, which allows to:
        - detect sudden changes in the signal
        - extract meaningful features that capture the signal's behavior within that window.
        - serve as a BCI input for classification tasks.

        Comment:
        Energy feature is defined as the sum of squared signal values within the window,
        Therefore, its value is closely related to the duration of the window.
        Energy comparisons between different window sizes may not be meaningful.

        Args:
            df: DataFrame containing EEG data.
            window_duration: Duration of each window in seconds.
            overlap: Overlap between consecutive windows in seconds.
        
        Returns:
        - times: ndarray
            Center times of each window.
        - rms_vec: ndarray
            Root Mean Square values for each window.
        - mav_vec: ndarray
            Mean Absolute Value for each window.
        - energy_vec: ndarray
            Total Energy for each window.
        """

        # 1. Convert df into a NP array for math consistency.
        signal = np.asarray(df)

        # 2. Convert the window duration into amount of data samples.
        window_size = int(window_duration * self.sampling_rate)

        # 3. Define the overlap or step within windows:
            # - overlap = 0.0  → step = window_length (sin solapamiento)
            # - overlap = 0.5  → step = window_length / 2

        step = int(window_size * 1 - overlap)

        # 4. Total number of samples in the data frame.
        n = len(signal)

        # 5. Compute starting index of each window (cut if incomplete)
        start_indexes = np.arange(0, n - window_size + 1, step)

        # 6. Initialize empty feature vectors.
        rms_vec = []
        mav_vec = []
        energy_vec = []
        times = []

        # Loop for extraction.abs
        for start in start_indexes:

            #1. extract segment
            segment = signal[start : start + window_size]

            # 2. rms
            rms = np.sqrt(np.mean(segment ** 2))

            # 3. mav
            mav = np.mean(np.abs(segment))

            # 4. total energy
            energy = np.sum(segment ** 2)

            # 5. center time of the window
            center_time = (start + window_size / 2) / self.sampling_rate

            # Append features to vectors
            rms_vec.append(rms)
            mav_vec.append(mav)
            energy_vec.append(energy)
            times.append(center_time)

        # Convert feature lists to numpy arrays
        rms_vec = np.array(rms_vec)
        mav_vec = np.array(mav_vec)
        energy_vec = np.array(energy_vec)
        times = np.array(times)

        return (
            times, 
            rms_vec, 
            mav_vec, 
            energy_vec
        )

    
    def plot_features(self, times, feature_values, feature_name, channel_name):
        """
        Plot extracted features over time.
        
        Args:
            times: ndarray
                Center times of each window.
            feature_values: list of ndarrays
                [0] Extracted feature values for each window.
                [1] Label or condition associated with each feature value (e.g., 'rest', 'motor').
            feature_name: str
                Name of the feature being plotted (e.g., 'RMS', 'MAV', 'Energy').
            channel_name: str
                Name of the EEG channel.
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 4))

        # If feature_values is 2D (multiple features), plot each
        for feature in feature_values:
            plt.plot(times, feature, label=f'{feature_name} - {feature_values[1]}')


        plt.title(f'Extracted {feature_name} for Channel: {channel_name}')
        plt.xlabel('Time (s)')
        plt.ylabel(feature_name)
        plt.grid()
        plt.show()
