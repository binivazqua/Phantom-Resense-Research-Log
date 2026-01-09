from scipy.signal import butter, lfilter, iirnotch
import numpy as np


class DataFilter:
    def __init__(self, lowcut=1.0, highcut=50.0, fs=256.0, notch_freq=60.0, quality_factor=30.0):
        self.lowcut = lowcut
        self.highcut = highcut
        self.fs = fs
        self.notch_freq = notch_freq
        self.quality_factor = quality_factor

    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = lfilter(b, a, data)
        return y

    def notch_filter(self, data, notch_freq, fs, quality_factor):
        nyq = 0.5 * fs
        norm_notch_freq = notch_freq / nyq
        b, a = iirnotch(norm_notch_freq, quality_factor)
        y = lfilter(b, a, data)
        return y

    def filter_data(self, dataframe):
        filtered_df = dataframe.copy()
        for column in filtered_df.columns:
            signal = filtered_df[column].values
            butter_signal = self.bandpass_filter(signal, self.lowcut, self.highcut, self.fs)
            notch_signal = self.notch_filter(butter_signal, self.notch_freq, self.fs, self.quality_factor)
            new_signal = notch_signal
            filtered_df[column] = new_signal
        return filtered_df
    