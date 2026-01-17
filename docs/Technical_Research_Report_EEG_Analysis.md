# Technical Research Report: Motor Intent EEG Analysis Project

**Date:** January 13, 2026  
**Hardware:** Muse 2 Headset  
**Purpose:** Research evaluation and methodology comparison

---

## 1. PROJECT OVERVIEW

### 1.1 Research Objectives

This project investigates motor intent and motor imagery detection using EEG signals acquired from a Muse 2 consumer-grade headset. The primary goal is to differentiate between four distinct cognitive states:

1. **Rest (Eyes Closed)** - Baseline with minimal visual input
2. **Rest (Eyes Open)** - Baseline with visual input, minimal artifacts
3. **Motor Intent** - Active execution of motor movement (e.g., right hand fist clenching)
4. **Motor Imagery** - Mental imagination of motor movement without physical execution

### 1.2 Hardware Specifications

- **Device:** Muse 2 EEG Headset
- **Sampling Rate:** 256 Hz
- **Electrode Configuration:** 4 channels (TP9, AF7, AF8, TP10)
- **Electrode Type:** Dry electrodes
- **Reference:** Fpz (forehead)
- **Connectivity:** Bluetooth via Lab Streaming Layer (LSL)

### 1.3 Research Context

Focus on **mu (8-13 Hz)** and **beta (13-30 Hz)** bands for motor cortex activity detection, consistent with established BCI research on event-related desynchronization (ERD) and synchronization (ERS).

---

## 2. DATA ACQUISITION METHODOLOGY

### 2.1 Experimental Protocol

#### Session Structure

- **Trial Duration:** 30 seconds per trial (configurable)
- **Trials per State:** 3 trials for each cognitive state (configurable)
- **Inter-Trial Rest:** 10 seconds between trials
- **Total Session Duration:** ~8-10 minutes (12 trials × 30s + rest periods)

#### State Sequence

The system uses a **blocked design** (not randomized by default) to minimize cognitive load and state confusion:

```
Block 1: Rest Eyes Closed (3 trials)
Block 2: Rest Eyes Open (3 trials)
Block 3: Motor Intent (3 trials)
Block 4: Motor Imagery (3 trials)
```

#### Trial Execution

1. **Pre-countdown:** Participant preparation
2. **3-second countdown:** Visual and auditory cues
3. **Recording:** 30-second EEG acquisition
4. **Audio feedback:** Trial completion signal
5. **Rest period:** 10-second recovery

### 2.2 Participant Guidance System

#### Audio Cue Integration

- **System:** macOS sound files (Glass, Ping, Tink)
- **Fallback:** Terminal bell for cross-platform compatibility
- **Purpose:** Minimize visual distractions during recording

#### Visual Instructions

```python
State Descriptions:
- "Rest with eyes closed - relax completely"
- "Rest with eyes open - stay calm, minimal blinking"
- "Motor Intent - EXECUTE the movement (e.g., clench fist)"
- "Motor Imagery - IMAGINE the movement (no actual movement)"
```

### 2.3 Data Collection Architecture

#### File Naming Convention

```
Format: {participant_id}_eeg_{state}_trial{number}_{movement_type}_{date}.csv

Examples:
- _001_eeg_rest_eyes_closed_trial01_right_hand_fist_20251220.csv
- _001_eeg_motor_intent_trial02_right_hand_fist_20251220.csv
- _001_eeg_motor_imagery_trial01_right_hand_fist_20251220.csv
```

#### Metadata Tracking

Each session generates:

1. **Quantitative Data:** Raw EEG CSV files (time-series voltage data)
2. **Qualitative Data:** Pre/post-session surveys
3. **Session Metadata:** Trial sequence, timestamps, configurations

#### LSL Integration

```python
# Streaming Pipeline
muselsl stream → LSL Protocol → muselsl record() → CSV output
```

---

## 3. SIGNAL PROCESSING PIPELINE

### 3.1 Frequency Band Extraction

#### Implemented Bands

```python
F_BANDS = {
    'delta': (0.5, 4),    # Deep sleep, unconscious processes
    'theta': (4, 8),      # Drowsiness, meditation
    'mu': (8, 13),        # Motor cortex idle/active (PRIMARY)
    'beta': (13, 30),     # Active thinking, motor planning (PRIMARY)
    'gamma': (30, 100),   # High-level cognition
}
```

#### Filter Specifications

- **Filter Type:** Butterworth bandpass filter
- **Filter Order:** 5 (configurable)
- **Implementation:** `scipy.signal.butter()` + `scipy.signal.lfilter()`
- **Nyquist Frequency:** 128 Hz (0.5 × sampling rate)

#### Mathematical Implementation

```
Normalized frequencies:
- low = lowcut / nyquist
- high = highcut / nyquist

Filter coefficients:
- b, a = butter(order=5, [low, high], btype='band')

Application:
- filtered_signal = lfilter(b, a, raw_signal)
```

### 3.2 Processing Workflow

```
Raw EEG Data (256 Hz)
        ↓
[Pre-processing: artifact removal, filtering]
        ↓
Frequency Band Extraction (FrequencyHandler)
        ↓
Mu Band (8-13 Hz) ← PRIMARY FOR MOTOR DETECTION
Beta Band (13-30 Hz) ← PRIMARY FOR MOTOR PLANNING
        ↓
[Feature Extraction] (feature_extraction.py)
        ↓
Classification/Analysis
```

### 3.3 Data Structure

#### Input Format

- **Type:** Pandas DataFrame
- **Columns:** EEG channels (TP9, AF7, AF8, TP10, timestamps)
- **Rows:** Time samples (256 samples/second)

#### Output Format

```python
{
    'mu': DataFrame(filtered_mu_signals),
    'beta': DataFrame(filtered_beta_signals),
    # Additional bands as needed
}
```

---

## 4. TECHNICAL IMPLEMENTATION DETAILS

### 4.1 Software Architecture

#### Class: `FrequencyHandler`

**Purpose:** Modular frequency band extraction and filtering

**Key Methods:**

1. `freqseg_bandpass(lowcut, highcut)` → Creates Butterworth filter coefficients
2. `apply_bandpass(data, lowcut, highcut)` → Applies filter to signal
3. `freq_extraction(dataframe, band)` → Extracts single frequency band
4. `extract_mult_bands(dataframe, bands)` → Batch extraction of multiple bands

**Design Philosophy:**

- Non-destructive (returns copies, preserves original data)
- Column-wise processing for multi-channel data
- Configurable sampling rate and filter order

#### Class: `MotorIntentDataAcquisition`

**Purpose:** End-to-end experiment management

**Key Features:**

1. Pre/post qualitative surveys for participant state tracking
2. Automated trial sequencing with audio/visual cues
3. Real-time LSL recording integration
4. Comprehensive metadata logging
5. Error handling and session recovery

### 4.2 Dependencies

```python
Core Libraries:
- mne: EEG data handling and analysis
- numpy: Numerical operations
- scipy.signal: Signal processing and filtering
- pandas: Data structuring and manipulation
- pylsl: Lab Streaming Layer integration
- muselsl: Muse-specific LSL wrapper
```

### 4.3 Environment

- **Python Version:** 3.13
- **Virtual Environment:** `muse_venv/`
- **OS:** macOS (with cross-platform considerations)

---

## 5. CURRENT PROJECT STATUS

### 5.1 Implemented Components

✅ Data acquisition system with audio cues  
✅ Frequency band extraction (5 standard bands)  
✅ LSL streaming integration  
✅ Multi-trial session management  
✅ Metadata and qualitative data collection  
✅ Butterworth bandpass filtering

### 5.2 Data Collected

- **Participants:** At least 1 (ID: 001)
- **Sessions:** Multiple recording sessions
- **Data Types:** Quantitative (EEG) and qualitative (surveys)
- **Storage:** Organized by date and condition

### 5.3 Next Steps (Implied)

🔄 Feature extraction implementation (`feature_extraction.py`)  
🔄 Statistical analysis of mu/beta band power  
🔄 Machine learning classification  
🔄 Event-related desynchronization (ERD) analysis  
🔄 Comparison with research literature

---

## 6. RESEARCH QUESTIONS FOR EVALUATION

### 6.1 Methodology Comparison

1. **Is the 256 Hz sampling rate from Muse 2 sufficient for mu/beta band analysis?**

   - Standard research EEG: 500-1000 Hz
   - Nyquist theorem: 256 Hz allows clean reconstruction up to 128 Hz

2. **How does 4-channel electrode placement compare to standard 10-20 system?**

   - Muse 2: TP9, AF7, AF8, TP10 (temporal/frontal focus)
   - Motor cortex coverage: C3, Cz, C4 (central) preferred for motor tasks
   - **Limitation:** Muse lacks central electrodes directly over motor cortex

3. **Are 30-second trials optimal for motor intent detection?**

   - Literature range: 3-10 seconds for single motor imagery trials
   - Longer trials may induce fatigue or attention drift

4. **Is the blocked design appropriate?**
   - Blocked: Easier for participants, potential order effects
   - Randomized: Controls for temporal confounds, more cognitively demanding

### 6.2 Signal Processing

5. **Is 5th-order Butterworth filter adequate?**

   - Higher orders: Sharper cutoff, potential ringing artifacts
   - Lower orders: Smoother response, wider transition bands

6. **Should notch filtering be applied for 60 Hz line noise?**

   - Not explicitly implemented in current pipeline

7. **Are artifact removal techniques needed?**
   - EOG (eye movement) artifacts particularly relevant for motor imagery
   - ICA (Independent Component Analysis) commonly used

### 6.3 Feature Extraction

8. **What features should be extracted from mu/beta bands?**

   - Band power (common)
   - Power spectral density (PSD)
   - Event-related desynchronization/synchronization (ERD/ERS)
   - Coherence between channels
   - Time-frequency analysis (wavelet transforms)

9. **What is the optimal time window for feature computation?**
   - Sliding windows vs. fixed epochs
   - Window length vs. frequency resolution trade-off

### 6.4 Classification

10. **What classification approach is most suitable?**
    - Classical ML: SVM, LDA, Random Forest
    - Deep Learning: CNN, RNN, LSTM
    - Riemannian geometry-based methods

---

## 7. COMPARISON WITH STANDARD BCI LITERATURE

### 7.1 Expected Phenomena

#### Mu Band (8-13 Hz)

- **ERD during motor execution:** Decrease in mu power over motor cortex
- **ERD during motor imagery:** Similar but weaker desynchronization
- **Rest condition:** Strong mu rhythm presence (synchronized)

#### Beta Band (13-30 Hz)

- **ERD during movement preparation and execution**
- **ERS (rebound) after movement termination**
- **Motor planning correlation**

### 7.2 Typical Feature Values

- **Baseline mu power:** Varies significantly between individuals
- **ERD magnitude:** 10-40% decrease from baseline
- **Lateralization:** Contralateral ERD stronger than ipsilateral

### 7.3 Classification Accuracy Benchmarks

- **Motor imagery (left vs. right hand):** 70-90% (research-grade EEG)
- **Consumer devices (Muse, Emotiv):** 60-75% reported accuracy
- **Rest vs. motor intent:** Generally higher accuracy than MI classification

---

## 8. TECHNICAL STRENGTHS OF CURRENT APPROACH

✅ **Reproducible protocol:** Standardized trial structure  
✅ **Participant-friendly:** Audio cues reduce experimenter bias  
✅ **Metadata rich:** Comprehensive logging for post-hoc analysis  
✅ **Modular design:** Reusable `FrequencyHandler` class  
✅ **Qualitative integration:** Subjective experience data captured  
✅ **Open-source stack:** MNE, SciPy, pandas (standard tools)

---

## 9. POTENTIAL LIMITATIONS TO EVALUATE

⚠️ **Electrode placement:** No central electrodes (C3, Cz, C4) for motor cortex  
⚠️ **Hardware constraints:** Consumer-grade vs. research-grade EEG  
⚠️ **Sample size:** Single or few participants (early stage)  
⚠️ **Artifact handling:** No explicit EOG/EMG removal implemented yet  
⚠️ **Validation:** No ground truth or comparison with established datasets  
⚠️ **Statistical analysis:** Power analysis, significance testing not yet apparent

---

## 10. QUESTIONS FOR GEMINI/NOTEBOOKLM ANALYSIS

### Please evaluate:

1. **How does this experimental design compare to published motor imagery BCI studies?**

   - Protocol similarities/differences
   - Standard practices I'm following or deviating from

2. **What are the implications of using temporal/frontal electrodes (TP9, AF7, AF8, TP10) instead of central electrodes (C3, Cz, C4)?**

   - Can motor cortex activity be reliably detected from these positions?
   - What alternative analysis approaches exist for frontal/temporal motor signals?

3. **What additional preprocessing steps are critical?**

   - Artifact rejection methods
   - Baseline correction approaches
   - Normalization techniques

4. **What feature extraction methods are most cited for mu/beta band motor tasks?**

   - Common Spatial Patterns (CSP)
   - Wavelet transforms
   - Hjorth parameters
   - Other domain-specific features

5. **How should I validate my results?**

   - Cross-validation strategies
   - Statistical tests for significance
   - Comparison with chance level
   - Reporting standards (e.g., decoding accuracy, confusion matrices)

6. **What are best practices for small sample size BCI research?**

   - Within-subject vs. across-subject analysis
   - Session-to-session variability handling

7. **Are there established benchmarks for Muse 2 specifically in motor imagery research?**

   - Published studies using same hardware
   - Expected performance ranges

8. **What improvements would have the highest impact on classification accuracy?**
   - Hardware upgrades
   - Protocol modifications
   - Algorithm choices

---

## 11. CODE REFERENCES

### Key Files

- **Data Acquisition:** `scripts/data_compiler_ui.py`
- **Frequency Extraction:** `scripts/frequency_handler.py`
- **Feature Extraction:** `scripts/feature_extraction.py` (in development)
- **Filtering:** `scripts/filtering_handler.py`, `scripts/filtering_main.py`

### Data Organization

```
new_data/
├── cuantitative/     # EEG time-series CSV files
└── cualitative/      # Survey responses and metadata

old_data/             # Previous experiments
```

---

## 12. EXPECTED OUTCOMES

### Research Goals

1. **Feasibility assessment:** Can Muse 2 detect motor intent reliably?
2. **Protocol optimization:** Refine trial structure for maximum signal quality
3. **Feature identification:** Determine most discriminative mu/beta features
4. **Classifier development:** Build subject-specific or general models

### Publication Potential

- Consumer-grade BCI validation study
- Motor intent vs. motor imagery discrimination
- Methodological comparison: temporal/frontal vs. central electrodes

---

## APPENDIX A: TECHNICAL SPECIFICATIONS SUMMARY

| Parameter      | Value                   | Standard Research     | Notes                         |
| -------------- | ----------------------- | --------------------- | ----------------------------- |
| Sampling Rate  | 256 Hz                  | 500-1000 Hz           | Sufficient for <100 Hz bands  |
| Channels       | 4 (TP9, AF7, AF8, TP10) | 64-256                | Limited spatial resolution    |
| Trial Duration | 30s                     | 3-10s                 | Longer than typical MI trials |
| Filter Type    | Butterworth             | Butterworth/Chebyshev | Standard choice               |
| Filter Order   | 5                       | 4-8                   | Moderate steepness            |
| Mu Band        | 8-13 Hz                 | 8-12 Hz               | Standard definition           |
| Beta Band      | 13-30 Hz                | 13-30 Hz              | Standard definition           |

---

## APPENDIX B: GLOSSARY

- **ERD:** Event-Related Desynchronization (power decrease)
- **ERS:** Event-Related Synchronization (power increase)
- **MI:** Motor Imagery
- **BCI:** Brain-Computer Interface
- **LSL:** Lab Streaming Layer
- **CSP:** Common Spatial Patterns
- **PSD:** Power Spectral Density
- **EOG:** Electrooculography (eye movement artifacts)
- **EMG:** Electromyography (muscle artifacts)

---

**End of Report**

_This document is intended for input to Gemini Notebook LM for comparative literature analysis and methodological evaluation._
