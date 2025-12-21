import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional


class EEGTrial:
    """
    Base class to handle a single EEG trial with plotting capabilities.
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize an EEG trial.
        
        Args:
            dataframe: DataFrame containing EEG data with timestamp and channel columns
        """
        self.df = dataframe
        self.timestamps = None  # TODO: Create numpy array from timestamp column
        self.sampling_rate = 256  # Muse 2 default
        
        # TODO: Extract timestamp data and convert to numpy array
        
    def plotchannel(self, channel: str, seconds: float):
        """
        Plot a specific channel for a given duration.
        
        Args:
            channel: Channel name ('TP9', 'AF7', 'AF8', 'TP10')
            seconds: Duration to plot in seconds
        """
        # TODO: Extract channel data for the specified duration
        # TODO: Create time array for x-axis
        # TODO: Plot using matplotlib
        pass
