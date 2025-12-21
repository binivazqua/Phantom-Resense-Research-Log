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
        duration = self.sampling_rate * seconds
        time_x = data_time[:duration]
        signal = self.df[channel][:duration]
        # TODO: Plot using matplotlib
        plt.figure(figsize=(10, 4))
        plt.plot(time_x, signal)
        plt.title(f'EEG Channel: {channel} for {seconds} seconds')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (µV)')
        plt.grid()
        plt.ylim(-200, 200)
        plt.show()

        return brain_plot # Return the plot object for further use if needed

    
    def saveplot(self, channel: str, seconds: float, filename: Optional[str] = None):
        """
        Save the plot of a specific channel for a given duration.
        
        Args:
            channel: Channel name
            seconds: Duration in seconds
            filename: Optional filename (default: 'channel_seconds.png')
        """
        plt.close('all')  # Close any existing plots first
        fig = self.plotchannel(channel, seconds)
        plt.close()  # Close the display
        
        if filename is None:
            filename = f"{channel}_{seconds}s.png"
        fig.savefig(filename)
        plt.close(fig)


