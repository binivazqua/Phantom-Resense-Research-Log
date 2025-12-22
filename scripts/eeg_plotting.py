import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional


class BrainPlotter:
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
        data_time = np.arange(len(self.df)) / self.sampling_rate
        duration = int(self.sampling_rate * seconds)
        time_x = data_time[:duration]
        signal = self.df[channel][:duration]
        # TODO: Plot using matplotlib
        fig = plt.figure(figsize=(10, 4))
        plt.plot(time_x, signal)
        plt.title(f'EEG Channel: {channel} for {seconds} seconds')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (µV)')
        plt.grid()
        plt.ylim(-600, 600)
        plt.show()

        return fig # Return the plot object for further use if needed
    
    def plot_multiple_channels(self, channels: [], seconds: float):
        
        offset = 300
        fig = plt.figure(figsize=(10,4))

        data_time = np.arange(len(self.df)) / self.sampling_rate
        duration = int(self.sampling_rate * seconds)
        time_x = data_time[:duration]


        for i, ch in enumerate(channels):
            signal = self.df[ch].values
            signal_points = signal[:duration]
            plt.plot(time_x, signal_points + i * offset, label=ch)
        
        plt.title(f'EEG Channels: {", ".join(channels)} for {seconds} seconds')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (µV)')
        plt.grid()
        plt.legend(loc='upper right')
        plt.ylim(-600, offset * len(channels))
        plt.show()

        return fig # Return the plot object for further use if needed
    
   


