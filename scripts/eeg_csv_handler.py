import pandas as pd
import numpy as np
from typing import List


class EEGFileHandling:
    """
    Simple class to handle loading Muse 2 CSV files for different trial types.
    """
    
    def __init__(self):
        """We unitialize the data loader with empty trial groups for good practice."""
        self.rest_eyes_open = []
        self.rest_eyes_closed = []
        self.motor_intent = []
        self.motor_imagery = []
    
    def load_trial_csvs(self, file_paths: List[str]) -> List[pd.DataFrame]:
        """
        Load a group of CSV files into a list of DataFrames.
        
        Args:
            file_paths: List of paths to CSV files
            
        Returns:
            List of pandas DataFrames
        """
        return [pd.read_csv(file) for file in file_paths]
    
    def load_all_data(self, rest_open_paths, rest_closed_paths, 
                      motor_intent_paths, motor_imagery_paths):
        """
        Load all trial groups at once.
        """
        self.rest_eyes_open = self.load_trial_csvs(rest_open_paths)
        self.rest_eyes_closed = self.load_trial_csvs(rest_closed_paths)
        self.motor_intent = self.load_trial_csvs(motor_intent_paths)
        self.motor_imagery = self.load_trial_csvs(motor_imagery_paths)
        
        print(f"Loaded {len(self.rest_eyes_open)} rest eyes open data.")
        print(f"Loaded {len(self.rest_eyes_closed)} rest eyes closed data.")
        print(f"Loaded {len(self.motor_intent)} motor intent data.")
        print(f"Loaded {len(self.motor_imagery)} motor imagery data.")



