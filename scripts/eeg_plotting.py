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
    
    def compare_plots(self, df_1, df_2, channel: str, seconds: float):
        """
        Compare the same channel from two different DataFrames over a specified duration.
        Args:
            df_1: First DataFrame containing EEG data (REST).
            df_2: Second DataFrame containing EEG data (ACTION).
            channel: Channel name to compare ('TP9', 'AF7', 'AF8', 'TP10')
            seconds: Duration to plot in seconds
        """
        
        data_time = np.arange(len(df_1)) / self.sampling_rate
        duration = int(self.sampling_rate * seconds)
        time_x = data_time[:duration]
        
        signal_1 = df_1[channel][:duration]
        signal_2 = df_2[channel][:duration]

        global_ymin = min(signal_1.min(), signal_2.min())
        global_ymax = max(signal_1.max(), signal_2.max())
        
        fig = plt.figure(figsize=(10, 4))
        plt.plot(time_x, signal_1, label='Trial 1')
        plt.plot(time_x, signal_2, label='Trial 2', alpha=0.7)
        plt.title(f'Comparison of EEG Channel: {channel} for {seconds} seconds')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (µV)')
        plt.grid()
        plt.legend()
        plt.ylim(global_ymin, global_ymax)
        plt.show()

        return fig # Return the plot object for further use if needed


