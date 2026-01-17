# Hybrid Motor Imagery Recording Feature

**Date:** January 17, 2026  
**Feature Version:** 1.0  
**Purpose:** Enhanced motor imagery detection with alternating active/rest periods

---

## OVERVIEW

The **Hybrid Motor Imagery** feature addresses key limitations identified in the technical research report by implementing shorter, alternating periods of motor imagery (MI) activity and rest within a single recording session. This approach is based on literature recommendations suggesting that 3-10 second trials are more effective than continuous 30-second recordings for motor imagery tasks.

### Key Improvements

✅ **Shorter MI periods** (5s) reduce participant fatigue and attention drift  
✅ **Structured rest periods** (10s) provide clear baseline comparisons  
✅ **Event labeling** in CSV for precise temporal segmentation  
✅ **Audio cues** guide participants through phase transitions  
✅ **Maintains existing infrastructure** - works alongside standard 30s recordings

---

## TECHNICAL SPECIFICATIONS

### Hybrid Trial Structure

```
┌─────────────────────────────────────────────────┐
│  Hybrid Motor Imagery Trial (30 seconds total) │
├─────────────────────────────────────────────────┤
│                                                 │
│  Cycle 1:                                       │
│    [MI: 5s] ───► [REST: 10s]                    │
│         ▲              ▲                        │
│      Audio cue    Audio cue                     │
│                                                 │
│  Cycle 2:                                       │
│    [MI: 5s] ───► [REST: 10s]                    │
│         ▲              ▲                        │
│      Audio cue    Audio cue                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Default Configuration

| Parameter                | Value      | Description                        |
| ------------------------ | ---------- | ---------------------------------- |
| `hybrid_mi_duration`     | 5 seconds  | Duration of motor imagery phase    |
| `hybrid_rest_duration`   | 10 seconds | Duration of rest phase             |
| `hybrid_cycles`          | 2          | Number of MI+REST cycles per trial |
| **Total trial duration** | 30 seconds | 2 × (5s + 10s)                     |

### CSV Output Format

The hybrid recording generates a labeled CSV file with the following structure:

```csv
TP9,AF7,AF8,TP10,timestamps,label
842.3,821.1,835.7,829.4,1705517280.123,MI
843.1,820.8,836.2,830.1,1705517280.127,MI
841.9,822.4,835.9,829.8,1705517280.131,MI
... [5 seconds of MI samples] ...
840.2,825.6,834.1,831.2,1705517285.142,REST
839.8,826.1,833.8,831.5,1705517285.146,REST
... [10 seconds of REST samples] ...
842.7,821.3,836.4,829.9,1705517295.287,MI
... [second cycle begins] ...
```

**Label Column:**

- `MI` - Motor Imagery active period (participant imagining movement)
- `REST` - Rest period (participant at rest)

---

## USAGE

### Running a Hybrid Motor Imagery Session

1. **Start the LSL stream** (in a separate terminal):

   ```bash
   muselsl stream
   ```

2. **Run the data acquisition script**:

   ```bash
   python scripts/data_compiler_ui.py
   ```

3. **Configure the session**:

   - When prompted, use default settings or customize as needed
   - The system will automatically include hybrid trials for the `motor_imagery_hybrid` state

4. **During recording**:
   - Audio cue **"Ping"** signals transition to Motor Imagery
   - Audio cue **"Ping"** signals transition to Rest
   - Visual terminal feedback shows current phase
   - Audio cue **"Tink"** (2 beeps) signals trial completion

### Example Session Sequence

```
Session Overview:
1. Rest Eyes Closed (3 trials × 30s each)
2. Rest Eyes Open (3 trials × 30s each)
3. Motor Intent (3 trials × 30s each)
4. Motor Imagery (3 trials × 30s continuous)
5. Motor Imagery Hybrid (3 trials × 30s with transitions) ← NEW
```

---

## IMPLEMENTATION DETAILS

### New State Added

```python
class MotorIntentState:
    MOTOR_IMAGERY_HYBRID = "motor_imagery_hybrid"
```

### Key Methods

#### `run_hybrid_trial(trial_info)`

Executes a hybrid motor imagery trial with the following steps:

1. Display trial information and countdown
2. Establish LSL stream connection
3. Record EEG data continuously
4. Apply event labels ("MI" or "REST") based on timing
5. Play audio cues at phase transitions
6. Save labeled CSV file

#### `AudioCues.phase_transition(phase_name)`

New audio cue specifically for within-trial phase changes:

```python
AudioCues.phase_transition("MOTOR IMAGERY")  # Signals start of MI period
AudioCues.phase_transition("REST")           # Signals start of rest period
```

### Configuration Parameters

Added to `SessionConfig` class:

```python
self.hybrid_mi_duration = 5       # seconds
self.hybrid_rest_duration = 10    # seconds
self.hybrid_cycles = 2            # cycles per trial
```

These can be adjusted programmatically or through future UI enhancements.

---

## DATA ANALYSIS CONSIDERATIONS

### Advantages for Analysis

1. **Precise temporal segmentation**: Each sample is labeled, enabling:

   - ERD/ERS analysis with exact phase boundaries
   - Direct comparison of MI vs REST within same trial
   - Reduced inter-trial variability

2. **Reduced fatigue effects**: Shorter MI periods (5s vs 30s) minimize:

   - Attention drift
   - Mental exhaustion
   - Performance degradation

3. **Built-in baselines**: REST periods immediately following MI periods provide:
   - Context-matched baseline
   - Better normalization for power calculations
   - ERS (event-related synchronization) detection

### Recommended Analysis Pipeline

```python
import pandas as pd

# Load hybrid trial data
df = pd.read_csv('_001_eeg_motor_imagery_hybrid_trial01_right_hand_fist_20251220.csv')

# Separate MI and REST samples
mi_data = df[df['label'] == 'MI']
rest_data = df[df['label'] == 'REST']

# Extract EEG channels
channels = ['TP9', 'AF7', 'AF8', 'TP10']
mi_eeg = mi_data[channels].values
rest_eeg = rest_data[channels].values

# Proceed with frequency analysis, feature extraction, etc.
```

### Feature Extraction Opportunities

- **Mu/Beta band power**: Compare MI vs REST periods
- **Event-Related Desynchronization (ERD)**: Calculate power decrease during MI
- **Event-Related Synchronization (ERS)**: Calculate power increase during REST
- **Temporal dynamics**: Analyze onset latencies and duration of ERD/ERS
- **Classification**: Train models on labeled segments

---

## COMPARISON WITH STANDARD APPROACH

| Aspect                   | Standard 30s Trial           | Hybrid Trial (5s+10s×2)     |
| ------------------------ | ---------------------------- | --------------------------- |
| Participant fatigue      | Higher (continuous 30s MI)   | Lower (only 10s total MI)   |
| Temporal precision       | Start/end only               | Sample-level labels         |
| Baseline comparison      | Separate trials              | Within-trial REST periods   |
| Literature alignment     | Longer than typical (3-10s)  | ✓ Matches 5s recommendation |
| Data preprocessing       | Requires manual segmentation | Pre-labeled                 |
| Classification potential | Trial-level only             | Segment-level possible      |

---

## TROUBLESHOOTING

### Issue: "No EEG stream found"

**Solution**: Ensure `muselsl stream` is running in another terminal before starting the script.

### Issue: Labels not appearing in CSV

**Solution**: Check that `pandas` is installed in your environment:

```bash
pip install pandas
```

### Issue: Audio cues not working (macOS)

**Solution**:

- Verify sound files exist in `/System/Library/Sounds/`
- Check system volume is not muted
- Falls back to terminal bell if sound files unavailable

### Issue: Recording stops prematurely

**Solution**:

- Check Muse 2 battery level
- Verify Bluetooth connection stability
- Ensure LSL stream is stable (no timeout errors)

---

## FUTURE ENHANCEMENTS

### Potential Improvements

1. **Configurable timing**: Add UI controls for custom MI/REST durations
2. **Visual feedback**: Real-time phase indicator on screen
3. **Randomized transitions**: Variable MI/REST periods to reduce anticipation
4. **Multi-movement support**: Different movements per cycle
5. **Real-time power visualization**: Display mu/beta band activity during recording
6. **Adaptive timing**: Adjust cycle length based on participant performance

### Research Directions

- Compare classification accuracy: Hybrid vs Standard trials
- Investigate optimal MI duration (3s vs 5s vs 7s)
- Analyze fatigue effects across multiple cycles
- Test with different rest durations (5s vs 10s vs 15s)

---

## REFERENCES

### Literature Support

- **Pfurtscheller & Neuper (2001)**: Motor imagery protocols typically use 3-6s cue periods
- **Blankertz et al. (2010)**: Shorter trials reduce fatigue in BCI systems
- **Lotte et al. (2018)**: Event-related designs improve temporal precision for ERD/ERS analysis

### Related Documentation

- [Technical Research Report](Technical_Research_Report_EEG_Analysis.md)
- [Tkinter Fix and Streaming Setup](Tkinter%20Fix%20and%20Streaming%20Setup.md)

---

## METADATA TRACKING

The system automatically logs detailed metadata for hybrid trials:

```python
{
    'trial': 15,
    'state': 'motor_imagery_hybrid',
    'trial_num_for_state': 1,
    'duration': '2 cycles',
    'mi_duration': 5,
    'rest_duration': 10,
    'cycles': 2,
    'filename': 'new_data/cuantitative/_001_eeg_motor_imagery_hybrid_trial01_...',
    'timestamp': '2026-01-17 14:32:45',
    'samples_collected': 7680,
    'mi_samples': 2560,
    'rest_samples': 5120
}
```

This enables:

- Session reproducibility
- Quality control (sample count verification)
- Batch analysis across multiple sessions

---

## CONCLUSION

The Hybrid Motor Imagery feature addresses critical limitations in consumer-grade EEG motor imagery research by:

1. ✅ Aligning with literature-recommended trial durations (5s)
2. ✅ Providing precise temporal labels for analysis
3. ✅ Reducing participant fatigue
4. ✅ Enabling within-trial baseline comparisons
5. ✅ Maintaining compatibility with existing data pipeline

**Result**: Improved signal quality, reduced artifacts, and enhanced classification potential for motor imagery BCI applications using the Muse 2 headset.

---

**For questions or issues, refer to the main project documentation or create an issue in the repository.**
