import mne, numpy as np, scipy.signal as signal, pandas as pd


class FrequencyHandler:
    """
        Custom class that segments previously filtered dfs into 
        desired frequency bands for analysis.
        This class is particularly updated to obtain Mu and Beta 
        bands for MI detection.

    """

    # THEORY TO-DATE FREQUENCY BANDS
    # Dictionary of tuples yay.
    F_BANDS = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'mu':(8, 13),
        'beta':(13, 30),
        'gamma':(30, 100),
    }

    def __init__(self, sfreq=256.0, bfilt_order=5):
        self.sfreq = sfreq
        self.bfilt_order = bfilt_order
        self.nyquist = 0.5 * sfreq
    
    def freqseg_bandpass(self, lowcut: float, highcut:float) -> tuple[np.ndarray, np.ndarray]:
        """
            Creates a specific Bandpass filter for frequency segmentation.
        """
        low = lowcut / self.nyquist
        high = highcut / self.nyquist
        b, a = signal.butter(self.bfilt_order, [low, high], btype='band')
        return b, a

    def apply_bandpass(self, data: np.ndarray, lowcut: float, highcut: float) -> np.ndarray:
        """
            Applies the bandpass filter to the data.
        """
        b, a = self.freqseg_bandpass(lowcut, highcut)
        y = signal.lfilter(b, a, data)
        return y
    
    def freq_extraction(self, dataframe, band: str) -> pd.DataFrame:
        """
            Extracts the desired frequency band from the dataframe.
        """
        if band not in self.F_BANDS:
            raise ValueError(f"Band '{band}' is misspelled. Available bands: {list(self.F_BANDS.keys())}")
        
        lowcut, highcut = self.F_BANDS[band]
        # create a copy to not mess with filtered data
        band_df = dataframe.copy()

        # apply bandpass to each column, and replace in dataframe
        for column in band_df.columns:
            signal = band_df[column].values
            bandpassed_signal = self.apply_bandpass(signal, lowcut, highcut)
            band_df[column] = bandpassed_signal
        
        return band_df
    
    def extract_mult_bands(self, dataframe, bands: list) -> dict:
        """
            Extracts multiple frequency bands from the dataframe.
            Returns a dictionary of dataframes.
        """
        band_dfs = {}
        for band in bands:
            band_dfs[band] = self.freq_extraction(dataframe, band)
        
        return band_dfs