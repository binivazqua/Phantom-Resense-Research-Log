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