# Working with Hybrid Data: Using Your Existing Architecture

**Date:** January 17, 2026  
**Purpose:** Guide for integrating labeled hybrid data with existing analysis pipeline

---

## OVERVIEW

Project's data handling architecture (`FrequencyHandler`, `FeatureExtractor`, `BrainPlotter`) is **fully compatible** with the hybrid motor imagery data format. The key difference is that hybrid CSV files include a `label` column that you can use to separate MI and REST segments before applying your existing analysis methods.

---

## QUICK START: The Pattern

```python
# 1. Load hybrid data
df = pd.read_csv('hybrid_trial.csv')

# NEW STEP!!! Is handy 'cause allows to analyze only contracortical data.
channels = ['TP9', 'AF7', 'AF8', 'TP10']
# 2. Separate by label
mi_data = df[df['label'] == 'MI'][channels]  # Only MI samples
rest_data = df[df['label'] == 'REST'][channels]  # Only REST samples

# 3. Use your existing tools as normal!
plotter = BrainPlotter(mi_data)
plotter.plotchannel('AF7', seconds=5)
```

All previouslyxisting classes work with the separated hybrid data.

---

## DETAILED WORKFLOWS

### Workflow 1: Frequency Band Analysis with FrequencyHandler

`FrequencyHandler` class works with labeled data after separation. Example here:

```python
import pandas as pd
from frequency_handler import FrequencyHandler

# Load hybrid trial
df = pd.read_csv('new_data/cuantitative/_001_eeg_motor_imagery_hybrid_trial01_right_hand_fist_20251220.csv')

# Define channels (exclude timestamps and label) --> HANDY
channels = ['TP9', 'AF7', 'AF8', 'TP10']

# Separate MI and REST ----- ONLY NEW ADDED STEP.
mi_data = df[df['label'] == 'MI'][channels].copy()
rest_data = df[df['label'] == 'REST'][channels].copy()

# Initialize FrequencyHandler
freq_handler = FrequencyHandler(sfreq=256)

# Extract mu and beta bands for MI period
mi_bands = freq_handler.extract_mult_bands(mi_data, ['mu', 'beta'])
mi_mu = mi_bands['mu']
mi_beta = mi_bands['beta']

# Extract mu and beta bands for REST period
rest_bands = freq_handler.extract_mult_bands(rest_data, ['mu', 'beta'])
rest_mu = rest_bands['mu']
rest_beta = rest_bands['beta']

print(f"MI mu band shape: {mi_mu.shape}")
print(f"REST mu band shape: {rest_mu.shape}")

# Now can create feature extraction.
```

**Key Points:**

- Extract `label` column BEFORE passing to FrequencyHandler
- Use `.copy()` to avoid SettingWithCopyWarning and keeping "original data" untouched.

---

### Workflow 2: Visualization with BrainPlotter

`BrainPlotter` class can visualize MI vs REST segments separately or compare them.

#### Plot MI Segment Only

```python
from eeg_plotting import BrainPlotter

# Load and separate
df = pd.read_csv('hybrid_trial.csv')
channels = ['TP9', 'AF7', 'AF8', 'TP10']
mi_data = df[df['label'] == 'MI'][channels].copy() # "Just extract the channels of the df where the labels are "MI"'

# Create plotter for MI data
mi_plotter = BrainPlotter(mi_data)

# Plot single channel (5 seconds of MI)
mi_plotter.plotchannel('AF7', seconds=5, title='Motor Imagery Phase')

# Plot multiple channels
mi_plotter.plot_multiple_channels(channels, seconds=5, title='Motor Imagery Phase')
```

#### Compare MI vs REST

```python
# Separate MI and REST
mi_data = df[df['label'] == 'MI'][channels].copy() # The same as above.
rest_data = df[df['label'] == 'REST'][channels].copy()

# Create plotter (can use either dataframe as base)
plotter = BrainPlotter(df)

# Use your existing compare_plots method!
plotter.compare_plots(
    df_1=rest_data,
    df_2=mi_data,
    channel='AF7',
    seconds=5,
    plot_type='overlap',  # or 'sidetoside'
    title='Hybrid Trial',
    df_1_alias='REST',
    df_2_alias='Motor Imagery'
)
```

---

### Workflow 3: Feature Extraction with FeatureExtractor

`FeatureExtractor` class computes RMS, MAV, and Energy features on windowed data. Based on the previous, we can analyze separately like this:

#### Extract Features from MI and REST Separately

```python
from feature_extraction import FeatureExtractor

# Load and separate
df = pd.read_csv('hybrid_trial.csv')
channels = ['TP9', 'AF7', 'AF8', 'TP10'] # can allow for only contracortical channels.
mi_data = df[df['label'] == 'MI'][channels].copy()
rest_data = df[df['label'] == 'REST'][channels].copy()

# Initialize feature extractors
mi_extractor = FeatureExtractor(mi_data)
rest_extractor = FeatureExtractor(rest_data)

# Extract features with 1-second windows, 50% overlap
window_duration = 1.0  # seconds
overlap = 0.5

# For a single channel (e.g., AF7)
channel_mi = mi_data['AF7']
channel_rest = rest_data['AF7']

# Extract MI features
times_mi, rms_mi, mav_mi, energy_mi = mi_extractor.window_feature_extraction(
    df=channel_mi,
    window_duration=window_duration,
    overlap=overlap
)

# Extract REST features
times_rest, rms_rest, mav_rest, energy_rest = rest_extractor.window_feature_extraction(
    df=channel_rest,
    window_duration=window_duration,
    overlap=overlap
)

print(f"MI windows: {len(times_mi)}")
print(f"REST windows: {len(times_rest)}")
```

#### Visualize Features

```python
# Plot RMS comparison using your existing plot_features method
mi_extractor.plot_features(
    time_rest=times_rest,
    time_active=times_mi,
    feature_val_rest=rms_rest,
    feature_val_active=rms_mi,
    feature_name='RMS',
    channel_name='AF7',
    title='Hybrid Trial'
)

# Plot MAV comparison
mi_extractor.plot_features(
    time_rest=times_rest,
    time_active=times_mi,
    feature_val_rest=mav_rest,
    feature_val_active=mav_mi,
    feature_name='MAV',
    channel_name='AF7',
    title='Hybrid Trial'
)
```

**Key Points:**

- The `window_feature_extraction()` works on 1D arrays, SO the syntax `channel_mi = mi_data['AF7']` is KEY.
- Time vectors for MI and REST will have different lengths (5s vs 10s)
- But `plot_features()` already handles different time vectors.

---

### Workflow 4: Normalization with FeatureExtractor

The `normalize_data()` method is ideal for hybrid trials since REST provides baseline.

```python
from feature_extraction import FeatureExtractor
from frequency_handler import FrequencyHandler

# Load and separate
df = pd.read_csv('hybrid_trial.csv')
channels = ['TP9', 'AF7', 'AF8', 'TP10']
mi_data = df[df['label'] == 'MI'][channels].copy()
rest_data = df[df['label'] == 'REST'][channels].copy()

# Extract mu band for both
freq_handler = FrequencyHandler()
mi_mu = freq_handler.freq_extraction(mi_data, 'mu')
rest_mu = freq_handler.freq_extraction(rest_data, 'mu')

# Normalize MI data using REST as baseline
extractor = FeatureExtractor(df)  # Base doesn't matter for normalization
normalized_rest, normalized_mi = extractor.normalize_data(
    rest_dataframe=rest_mu,
    motor_dataframe=mi_mu
)

print("MI data normalized using REST baseline")

#Extra: print some basic featrues.
print(f"Normalized MI mean: {normalized_mi.mean().mean():.4f}")
print(f"Normalized REST mean: {normalized_rest.mean().mean():.4f}")
```

**Key Points:**

- REST periods from same trial = perfect baseline
- Reduces inter-trial variability

---

## COMPLETE ANALYSIS PIPELINE

Here's a full example combining all existing tools:

```python
#!/usr/bin/env python3


import pandas as pd
import numpy as np
from frequency_handler import FrequencyHandler
from feature_extraction import FeatureExtractor
from eeg_plotting import BrainPlotter

# ===== 1. LOAD AND SEPARATE =====
print("Loading hybrid trial data...")
df = pd.read_csv('new_data/cuantitative/_001_eeg_motor_imagery_hybrid_trial01_right_hand_fist_20251220.csv')

channels = ['TP9', 'AF7', 'AF8', 'TP10']
mi_data = df[df['label'] == 'MI'][channels].copy()
rest_data = df[df['label'] == 'REST'][channels].copy()

print(f"✓ MI samples: {len(mi_data)} ({len(mi_data)/256:.2f}s)")
print(f"✓ REST samples: {len(rest_data)} ({len(rest_data)/256:.2f}s)")

# ===== 2. FREQUENCY BAND EXTRACTION =====
print("\nExtracting frequency bands...")
freq_handler = FrequencyHandler(sfreq=256)

# Extract mu and beta for both conditions
mi_bands = freq_handler.extract_mult_bands(mi_data, ['mu', 'beta'])
rest_bands = freq_handler.extract_mult_bands(rest_data, ['mu', 'beta'])

mi_mu = mi_bands['mu']
mi_beta = mi_bands['beta']
rest_mu = rest_bands['mu']
rest_beta = rest_bands['beta']

print("✓ Frequency bands extracted")

# ===== 3. NORMALIZE USING REST BASELINE =====
print("\nNormalizing data...")
extractor = FeatureExtractor(df)
norm_rest_mu, norm_mi_mu = extractor.normalize_data(rest_mu, mi_mu)
norm_rest_beta, norm_mi_beta = extractor.normalize_data(rest_beta, mi_beta)
print("✓ Data normalized")

# ===== 4. COMPUTE BAND POWER =====
print("\nComputing band power...")

def compute_power(dataframe):
    """Compute average power across all channels"""
    return np.mean(dataframe.values ** 2, axis=0)

mi_mu_power = compute_power(norm_mi_mu)
rest_mu_power = compute_power(norm_rest_mu)
mi_beta_power = compute_power(norm_mi_beta)
rest_beta_power = compute_power(norm_rest_beta)

# ===== 5. COMPUTE ERD/ERS =====
print("\nComputing ERD/ERS...")

def compute_erd_ers(mi_power, rest_power):
    """ERD% = ((MI - REST) / REST) * 100"""
    return ((mi_power - rest_power) / rest_power) * 100

mu_erd_ers = compute_erd_ers(mi_mu_power, rest_mu_power)
beta_erd_ers = compute_erd_ers(mi_beta_power, rest_beta_power)

print("\nMu Band ERD/ERS (%):")
for i, ch in enumerate(channels):
    print(f"  {ch}: {mu_erd_ers[i]:6.2f}%")

print("\nBeta Band ERD/ERS (%):")
for i, ch in enumerate(channels):
    print(f"  {beta_erd_ers[i]:6.2f}%")

# ===== 6. FEATURE EXTRACTION =====
print("\nExtracting windowed features...")

# For AF7 channel (you can loop through all channels)
mi_af7 = mi_mu['AF7']
rest_af7 = rest_mu['AF7']

mi_feat_extractor = FeatureExtractor(pd.DataFrame(mi_af7))
rest_feat_extractor = FeatureExtractor(pd.DataFrame(rest_af7))

times_mi, rms_mi, mav_mi, energy_mi = mi_feat_extractor.window_feature_extraction(
    df=mi_af7, window_duration=1.0, overlap=0.5
)

times_rest, rms_rest, mav_rest, energy_rest = rest_feat_extractor.window_feature_extraction(
    df=rest_af7, window_duration=1.0, overlap=0.5
)

print(f"✓ MI windows: {len(times_mi)}")
print(f"✓ REST windows: {len(times_rest)}")

# ===== 7. VISUALIZATION =====
print("\nGenerating visualizations...")

# Plot 1: Raw signal comparison
plotter = BrainPlotter(df)
plotter.compare_plots(
    df_1=rest_data,
    df_2=mi_data,
    channel='AF7',
    seconds=5,
    plot_type='overlap',
    title='Hybrid Trial (Mu Band)',
    df_1_alias='REST',
    df_2_alias='Motor Imagery'
)

# Plot 2: Frequency band comparison (mu band)
plotter_mu = BrainPlotter(df)
plotter_mu.compare_plots(
    df_1=rest_mu,
    df_2=mi_mu,
    channel='AF7',
    seconds=5,
    plot_type='sidetoside',
    title='Mu Band (8-13 Hz)',
    df_1_alias='REST',
    df_2_alias='Motor Imagery'
)

# Plot 3: Features comparison
mi_feat_extractor.plot_features(
    time_rest=times_rest,
    time_active=times_mi,
    feature_val_rest=rms_rest,
    feature_val_active=rms_mi,
    feature_name='RMS',
    channel_name='AF7 (Mu Band)',
    title='Hybrid Trial'
)

print("\n✓ Analysis complete!")
```

---

## WHEN TO USE HYBRID vs STANDARD DATA

| Use Case                             | Recommended Format          |
| ------------------------------------ | --------------------------- |
| Within-trial baseline comparison     | **Hybrid** ✓                |
| Long continuous motor imagery        | Standard                    |
| ERD/ERS analysis with precise timing | **Hybrid** ✓                |
| Fatigue assessment                   | Standard (30s)              |
| Classification with short epochs     | **Hybrid** ✓                |
| Resting state analysis               | Standard (eyes closed/open) |
| Multi-cycle motor tasks              | **Hybrid** ✓                |

---

## STATE TRANSITION ANALYSIS

### Why Transition Analysis Matters for Real-Time BCI

In real-time motor imagery detection, you need to identify **when** motor imagery starts and stops, not just recognize it after the fact. Hybrid trials provide perfectly labeled transition points between REST and MI states, making them ideal for:

1. **Training transition detectors** - Learn what neural signatures indicate MI onset/offset
2. **Measuring latency** - How quickly does ERD/ERS appear after state change?
3. **Feature selection** - Which features respond fastest to state changes?
4. **Real-time thresholds** - Determine decision boundaries for online classification

### Understanding Transition Windows

Hybrid data has **4 critical transition points** per cycle:

```
REST → MI (onset)     ← Critical for real-time detection
MI → REST (offset)    ← Useful for understanding ERS rebound
REST → MI (onset)     ← Second cycle
MI → REST (offset)    ← Second cycle
```

### Extracting Transition Periods

```python
import pandas as pd
import numpy as np

def extract_transitions(df, channels, window_before=1.0, window_after=1.0, fs=256):
    """
    Extract transition periods from hybrid data

    Args:
        df: Full hybrid trial dataframe with 'label' column
        channels: List of EEG channel names
        window_before: Seconds before transition (default 1.0)
        window_after: Seconds after transition (default 1.0)
        fs: Sampling rate (default 256 Hz)

    Returns:
        dict: Transition segments and metadata
    """

    # Find transition indices
    label_changes = df['label'].ne(df['label'].shift()).to_numpy()
    transition_indices = np.where(label_changes)[0]

    # Skip first index (start of recording)
    transition_indices = transition_indices[1:]

    samples_before = int(window_before * fs)
    samples_after = int(window_after * fs)

    transitions = {
        'rest_to_mi': [],
        'mi_to_rest': []
    }

    for idx in transition_indices:
        # Skip if too close to boundaries
        if idx < samples_before or idx + samples_after >= len(df):
            continue

        # Extract window around transition
        start = idx - samples_before
        end = idx + samples_after
        segment = df.iloc[start:end][channels].copy()

        # Determine transition type
        state_after = df.iloc[idx]['label']
        if state_after == 'MI':
            transition_type = 'rest_to_mi'
        else:
            transition_type = 'mi_to_rest'

        transitions[transition_type].append({
            'data': segment,
            'transition_idx': idx,
            'samples_before': samples_before,
            'samples_after': samples_after,
            'time_before': window_before,
            'time_after': window_after
        })

    return transitions

# Usage
df = pd.read_csv('hybrid_trial.csv')
channels = ['TP9', 'AF7', 'AF8', 'TP10']

transitions = extract_transitions(df, channels, window_before=1.0, window_after=2.0)

print(f"REST→MI transitions found: {len(transitions['rest_to_mi'])}")
print(f"MI→REST transitions found: {len(transitions['mi_to_rest'])}")
```

### Workflow: Analyzing REST → MI Transitions

This is the most critical transition for real-time detection.

```python
from frequency_handler import FrequencyHandler
import matplotlib.pyplot as plt

# Extract transitions
transitions = extract_transitions(df, channels, window_before=1.0, window_after=2.0)
rest_to_mi = transitions['rest_to_mi']

# Analyze first transition
transition_data = rest_to_mi[0]['data']
samples_before = rest_to_mi[0]['samples_before']

# Extract mu band
freq_handler = FrequencyHandler()
mu_band = freq_handler.freq_extraction(transition_data, 'mu')

# Compute sliding window power (250ms windows)
window_size = int(0.25 * 256)  # 250ms
power_timeline = []
times = []

for i in range(0, len(mu_band) - window_size, window_size // 2):
    window = mu_band.iloc[i:i+window_size].values
    power = np.mean(window ** 2)  # Average power across all channels
    power_timeline.append(power)
    times.append((i - samples_before) / 256)  # Time relative to transition

# Plot power evolution around transition
plt.figure(figsize=(12, 6))
plt.plot(times, power_timeline, linewidth=2, color='blue')
plt.axvline(0, color='red', linestyle='--', linewidth=2, label='Transition Point (REST→MI)')
plt.axvspan(-1, 0, alpha=0.2, color='cyan', label='REST period')
plt.axvspan(0, 2, alpha=0.2, color='orange', label='MI period')
plt.xlabel('Time relative to transition (s)', fontsize=12)
plt.ylabel('Mu Band Power (μV²)', fontsize=12)
plt.title('Mu Band Power Evolution During REST → MI Transition', fontsize=14, fontweight='bold')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)
plt.show()
```

### Computing Transition Latency

**Latency** = Time between transition point and detectable change in neural activity.

```python
def compute_erd_onset_latency(transition_segment, baseline_window=1.0,
                               detection_threshold=0.10, fs=256):
    """
    Compute ERD onset latency after REST→MI transition

    Args:
        transition_segment: DataFrame with transition data
        baseline_window: Seconds of baseline before transition (default 1.0s)
        detection_threshold: Percentage change to detect ERD (default 10%)
        fs: Sampling rate

    Returns:
        float: Latency in seconds (or None if not detected)
    """
    from frequency_handler import FrequencyHandler

    # Extract mu band
    freq_handler = FrequencyHandler()
    mu_band = freq_handler.freq_extraction(transition_segment, 'mu')

    # Compute baseline power (before transition)
    baseline_samples = int(baseline_window * fs)
    baseline_data = mu_band.iloc[:baseline_samples].values
    baseline_power = np.mean(baseline_data ** 2)

    # Compute sliding power after transition (50ms windows)
    window_size = int(0.05 * fs)  # 50ms

    for i in range(baseline_samples, len(mu_band) - window_size, window_size):
        window = mu_band.iloc[i:i+window_size].values
        current_power = np.mean(window ** 2)

        # Check for ERD (power decrease)
        power_change = (current_power - baseline_power) / baseline_power

        if power_change < -detection_threshold:  # Negative = desynchronization
            latency = (i - baseline_samples) / fs
            return latency

    return None  # ERD not detected

# Analyze latency for all REST→MI transitions
rest_to_mi = transitions['rest_to_mi']
latencies = []

for trans in rest_to_mi:
    latency = compute_erd_onset_latency(trans['data'])
    if latency is not None:
        latencies.append(latency)
        print(f"ERD onset detected at {latency:.3f}s after transition")

if latencies:
    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)
    print(f"\nAverage ERD onset latency: {avg_latency:.3f} ± {std_latency:.3f}s")
else:
    print("\nNo clear ERD detected in transitions")
```

### Feature-Based Transition Detection

Extract features around transitions to identify discriminative patterns.

```python
from feature_extraction import FeatureExtractor

def extract_transition_features(transitions, feature_type='rms'):
    """
    Extract features from all transitions for comparison

    Args:
        transitions: Dict from extract_transitions()
        feature_type: 'rms', 'mav', or 'energy'

    Returns:
        dict: Features for each transition type
    """
    from frequency_handler import FrequencyHandler

    freq_handler = FrequencyHandler()

    feature_dict = {
        'rest_to_mi': [],
        'mi_to_rest': []
    }

    for trans_type, trans_list in transitions.items():
        for trans in trans_list:
            # Extract mu band
            mu_data = freq_handler.freq_extraction(trans['data'], 'mu')

            # Extract features for each channel
            channel_features = {}
            for channel in mu_data.columns:
                extractor = FeatureExtractor(pd.DataFrame(mu_data[channel]))
                times, rms, mav, energy = extractor.window_feature_extraction(
                    df=mu_data[channel],
                    window_duration=0.25,  # 250ms windows
                    overlap=0.5
                )

                if feature_type == 'rms':
                    channel_features[channel] = rms
                elif feature_type == 'mav':
                    channel_features[channel] = mav
                elif feature_type == 'energy':
                    channel_features[channel] = energy

            feature_dict[trans_type].append({
                'features': channel_features,
                'times': times,
                'transition_idx': trans['transition_idx']
            })

    return feature_dict

# Extract RMS features around transitions
transition_features = extract_transition_features(transitions, feature_type='rms')

# Analyze REST→MI transitions
rest_to_mi_features = transition_features['rest_to_mi']

# Average RMS across all REST→MI transitions for AF7
af7_rms_all = []
for trans in rest_to_mi_features:
    af7_rms_all.append(trans['features']['AF7'])

af7_rms_avg = np.mean(af7_rms_all, axis=0)
times = rest_to_mi_features[0]['times']

# Find transition point in time vector
transition_time = 0  # Relative to our extraction window

# Plot
plt.figure(figsize=(12, 6))
plt.plot(times, af7_rms_avg, linewidth=2, color='purple')
plt.axvline(transition_time, color='red', linestyle='--', linewidth=2,
            label='Transition (REST→MI)')
plt.xlabel('Time (s)', fontsize=12)
plt.ylabel('RMS (μV)', fontsize=12)
plt.title('Average RMS Evolution During REST→MI Transition (AF7, Mu Band)',
          fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Preparing for Real-Time Detection

Based on transition analysis, Claude reccs this RT Detector:

```python
class RealtimeMotorImageryDetector:
    """
    Template for real-time MI detection based on transition analysis
    """

    def __init__(self, channels, detection_threshold=-0.15,
                 baseline_duration=1.0, detection_window=0.5):
        """
        Initialize detector with parameters learned from transition analysis

        Args:
            channels: EEG channel names
            detection_threshold: ERD percentage threshold (e.g., -0.15 = 15% decrease)
            baseline_duration: Rolling baseline window (seconds)
            detection_window: Window for power computation (seconds)
        """
        self.channels = channels
        self.detection_threshold = detection_threshold
        self.baseline_duration = baseline_duration
        self.detection_window = detection_window
        self.fs = 256

        # Initialize buffers
        self.baseline_buffer = []
        self.detection_buffer = []

        # State tracking
        self.current_state = 'REST'
        self.state_confidence = 0.0

    def update(self, new_sample):
        """
        Process new EEG sample (in real-time this would be called continuously)

        Args:
            new_sample: Dict or array with channel values

        Returns:
            tuple: (detected_state, confidence)
        """
        from frequency_handler import FrequencyHandler

        # Add to buffers
        self.baseline_buffer.append(new_sample)
        self.detection_buffer.append(new_sample)

        # Maintain buffer sizes
        baseline_samples = int(self.baseline_duration * self.fs)
        detection_samples = int(self.detection_window * self.fs)

        if len(self.baseline_buffer) > baseline_samples:
            self.baseline_buffer.pop(0)
        if len(self.detection_buffer) > detection_samples:
            self.detection_buffer.pop(0)

        # Only detect when buffers are full
        if len(self.baseline_buffer) < baseline_samples:
            return self.current_state, 0.0
        if len(self.detection_buffer) < detection_samples:
            return self.current_state, 0.0

        # Convert to DataFrame and extract mu band
        baseline_df = pd.DataFrame(self.baseline_buffer, columns=self.channels)
        detection_df = pd.DataFrame(self.detection_buffer, columns=self.channels)

        freq_handler = FrequencyHandler()
        baseline_mu = freq_handler.freq_extraction(baseline_df, 'mu')
        detection_mu = freq_handler.freq_extraction(detection_df, 'mu')

        # Compute power
        baseline_power = np.mean(baseline_mu.values ** 2)
        detection_power = np.mean(detection_mu.values ** 2)

        # Compute relative change
        power_change = (detection_power - baseline_power) / baseline_power

        # Determine state
        if power_change < self.detection_threshold:
            detected_state = 'MI'
            confidence = abs(power_change)
        else:
            detected_state = 'REST'
            confidence = 1.0 - abs(power_change)

        self.current_state = detected_state
        self.state_confidence = confidence

        return detected_state, confidence

    def reset(self):
        """Reset detector state"""
        self.baseline_buffer = []
        self.detection_buffer = []
        self.current_state = 'REST'
        self.state_confidence = 0.0

# Example usage (with simulated real-time data)
detector = RealtimeMotorImageryDetector(
    channels=['TP9', 'AF7', 'AF8', 'TP10'],
    detection_threshold=-0.15,  # Learned from transition analysis
    baseline_duration=1.0,
    detection_window=0.5
)

# Simulate processing hybrid trial in "real-time"
df = pd.read_csv('hybrid_trial.csv')
channels = ['TP9', 'AF7', 'AF8', 'TP10']

detected_states = []
true_labels = []
confidences = []

for idx, row in df.iterrows():
    sample = row[channels].values
    true_label = row['label']

    detected_state, confidence = detector.update(sample)

    detected_states.append(detected_state)
    true_labels.append(true_label)
    confidences.append(confidence)

# Compute detection accuracy
correct = sum([1 for d, t in zip(detected_states, true_labels) if d == t])
accuracy = correct / len(detected_states) * 100

print(f"\nReal-time detection accuracy: {accuracy:.2f}%")
```

### Key Insights from Transition Analysis

#### 1. **Optimal Detection Thresholds**

From your transition analysis, determine:

- Minimum ERD percentage that reliably indicates MI
- Optimal baseline window length
- Detection window size for best accuracy vs. latency tradeoff

#### 2. **Channel Selection**

Some channels may show faster or stronger transitions:

```python
# Compare transition speeds across channels
for channel in channels:
    channel_latencies = []
    for trans in rest_to_mi:
        channel_data = trans['data'][[channel]]
        latency = compute_erd_onset_latency(channel_data)
        if latency:
            channel_latencies.append(latency)

    if channel_latencies:
        print(f"{channel}: {np.mean(channel_latencies):.3f}s avg latency")
```

#### 3. **False Positive Rates**

Analyze MI→REST transitions to understand ERS rebound and avoid false detections:

```python
mi_to_rest = transitions['mi_to_rest']
# Expect ERS (power increase) after MI ends
# Set thresholds to avoid detecting this as new MI onset
```

### Practical Recommendations

✅ **For Training Data Collection:**

- Use hybrid trials (labeled transitions are gold standard)
- Collect at least 20-30 transitions per participant
- Vary MI duration to test detector robustness

✅ **For Real-Time Parameters:**

- Baseline window: 0.5-1.0s (balance stability vs. responsiveness)
- Detection window: 0.25-0.5s (shorter = faster, but noisier)
- Threshold: Start at -10% ERD, adjust based on participant

✅ **For Validation:**

- Use transition analysis to set initial parameters
- Fine-tune with cross-validation on full trials
- Test on separate session data (generalization)

---

**Happy analyzing!**
