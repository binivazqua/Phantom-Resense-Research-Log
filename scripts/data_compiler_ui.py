#!/usr/bin/env python3
"""
Motor Intent EEG Data Acquisition Interface
============================================
Research-oriented script for labeled EEG data collection with Muse 2 headset.

States:
  - Rest (Eyes Closed)
  - Rest (Eyes Open)
  - Motor Intent
  - Motor Imagery
  - Motor Imagery Hybrid (NEW) - Alternating 5s MI + 10s REST with labels

Features:
  - Audio cues for state transitions
  - Automatic session progression
  - Integration with EEGRecorder
  - Pre-session qualitative survey
  - Labeled data files for ML training
  - Within-trial phase labeling for hybrid recordings

PREREQUISITE: Must have 'muselsl stream' running in another terminal
"""

import sys
import time
import csv
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# Import existing classes
sys.path.append(str(Path(__file__).parent))
from eeg_recording import EEGRecorder
from variable_handling import CualitativeSurvey


# ============================================
# AUDIO CUE SYSTEM
# ============================================

class AudioCues:
    """Handles all audio feedback for the experiment"""
    
    @staticmethod
    def play_beep(count=1, sound_file=None):
        """
        Play system beep or sound file
        
        Args:
            count: Number of beeps (for terminal bell)
            sound_file: macOS sound file name (e.g., 'Ping', 'Glass', 'Tink')
        """
        system = platform.system()
        
        if system == "Darwin" and sound_file:  # macOS
            try:
                sound_path = f"/System/Library/Sounds/{sound_file}.aiff"
                subprocess.run(["afplay", sound_path], check=False, timeout=2)
                return
            except:
                pass
        
        # Fallback to terminal bell
        for _ in range(count):
            print("\a", end="", flush=True)
            if count > 1:
                time.sleep(0.2)
    
    @staticmethod
    def session_start():
        """Sound cue for session beginning"""
        print("******* [SESSION START] *******")
        AudioCues.play_beep(sound_file="Glass")
    
    @staticmethod
    def state_transition(state_name):
        """Sound cue for entering a new state"""
        print(f"***** [ENTERING: {state_name}] *****")
        AudioCues.play_beep(sound_file="Ping")
    
    @staticmethod
    def recording_complete():
        """Sound cue for trial completion"""
        print("***** [RECORDING COMPLETE] *****")
        AudioCues.play_beep(count=2, sound_file="Tink")
    
    @staticmethod
    def session_end():
        """Sound cue for session ending"""
        print("***** [SESSION END] *****")
        AudioCues.play_beep(sound_file="Glass")
    
    @staticmethod
    def phase_transition(phase_name):
        """Sound cue for phase changes within hybrid trial (MI -> REST or REST -> MI)"""
        print(f">>> [TRANSITION: {phase_name}] <<<")
        AudioCues.play_beep(count=1, sound_file="Ping")


# ============================================
# MOTOR INTENT DATA ACQUISITION SYSTEM
# ============================================

class MotorIntentState:
    """Defines the states for motor intent research"""
    REST_EYES_CLOSED = "rest_eyes_closed"
    REST_EYES_OPEN = "rest_eyes_open"
    MOTOR_INTENT = "motor_intent"
    MOTOR_IMAGERY = "motor_imagery"
    MOTOR_IMAGERY_HYBRID = "motor_imagery_hybrid"
    
    @classmethod
    def all_states(cls):
        return [
            cls.REST_EYES_CLOSED,
            cls.REST_EYES_OPEN,
            cls.MOTOR_INTENT,
            cls.MOTOR_IMAGERY,
            cls.MOTOR_IMAGERY_HYBRID
        ]
    
    @classmethod
    def get_description(cls, state):
        descriptions = {
            cls.REST_EYES_CLOSED: "Rest with eyes closed - relax completely",
            cls.REST_EYES_OPEN: "Rest with eyes open - stay calm, minimal blinking",
            cls.MOTOR_INTENT: "Motor Intent - EXECUTE the movement (e.g., clench fist)",
            cls.MOTOR_IMAGERY: "Motor Imagery - IMAGINE the movement (no actual movement)",
            cls.MOTOR_IMAGERY_HYBRID: "Hybrid Motor Imagery - Alternating 5s IMAGINE + 10s REST periods"
        }
        return descriptions.get(state, "Unknown state")


class SessionConfig:
    """Configuration for a data acquisition session"""
    def __init__(self):
        self.participant_id = "000"
        self.session_name = "motor_intent_session"
        self.trial_duration = 30  # seconds per trial
        self.trials_per_state = 3  # Number of trials for each state
        self.rest_between_trials = 10  # seconds
        self.movement_type = "right_hand_fist"  # Type of motor task
        
        # Hybrid trial configuration
        self.hybrid_mi_duration = 5  # seconds of motor imagery
        self.hybrid_rest_duration = 10  # seconds of rest
        self.hybrid_cycles = 2  # number of MI+REST cycles per hybrid trial
        
    def get_total_trials(self):
        return len(MotorIntentState.all_states()) * self.trials_per_state
    
    def get_hybrid_total_duration(self):
        """Calculate total duration for one hybrid trial"""
        return self.hybrid_cycles * (self.hybrid_mi_duration + self.hybrid_rest_duration)


class MotorIntentDataAcquisition:
    """
    Main class for conducting motor intent EEG data acquisition sessions
    """
    def __init__(self, config: SessionConfig):
        self.config = config
        self.current_trial = 0
        self.trial_sequence = []
        self.session_metadata = []
        self.recorder = None
        self.survey = None
        self.initial_response = None
        
    def generate_trial_sequence(self):
        """Generate randomized or blocked trial sequence"""
        sequence = []
        
        # Create trials for each state
        for state in MotorIntentState.all_states():
            for trial_num in range(self.config.trials_per_state):
                sequence.append({
                    'state': state,
                    'trial_num': trial_num + 1,
                    'duration': self.config.trial_duration
                })
        
        
        # import random
        # random.shuffle(sequence)
        
        self.trial_sequence = sequence
        return sequence
    
    def conduct_pre_session_survey(self):
        """Collect qualitative data before session"""

        print("\n" + "="*60)
        print("======== PRE-SESSION QUALITATIVE SURVEY ========")
        print("="*60)
        
        self.survey = CualitativeSurvey(
            filename=f"prueba_{self.config.participant_id}_{self.config.session_name}",
            p_id=self.config.participant_id
        )
        self.survey.init_csv()
        self.initial_response = self.survey.ask_initial_survey()
        
        print("\n===== Pre-session survey COMPLETED ======\n")
        time.sleep(1)
    
    def conduct_post_session_survey(self):
        """Collect qualitative data after session"""
        
        print("\n" + "="*60)
        print("======== POST-SESSION QUALITATIVE SURVEY ========")
        print("="*60)
        
        final_response = self.survey.ask_final_survey()
        self.survey.save_survey_response(self.initial_response, final_response)
        
        print("\n===== Post-session survey COMPLETED ======\n")
        time.sleep(1)
    
    def display_session_info(self):
        """Show session overview to participant"""

        print("\n" + "="*60)
        print("  SESSION OVERVIEW")
        print("="*60)
        print(f"Participant ID: {self.config.participant_id}")
        print(f"Session Name: {self.config.session_name}")
        print(f"Movement Type: {self.config.movement_type}")
        print(f"Total Trials: {self.config.get_total_trials()}")
        print(f"Trial Duration: {self.config.trial_duration}s")
        print(f"Trials per State: {self.config.trials_per_state}")
        print("\nStates to be recorded:")
        for i, state in enumerate(MotorIntentState.all_states(), 1):
            print(f"  {i}. {state}: {MotorIntentState.get_description(state)}")
        print("="*60 + "\n")
        
        input("Press [ENTER] when ready to begin...")
    
    def run_hybrid_trial(self, trial_info):
        """Execute a hybrid motor imagery trial with alternating MI and REST periods with audio ques and added labels to the output data."""
        state = trial_info['state']
        trial_num = trial_info['trial_num']
        
        self.current_trial += 1
        total_trials = self.config.get_total_trials()
        
        print("\n" + "-"*60)
        print(f"  HYBRID TRIAL {self.current_trial}/{total_trials}")
        print(f"  State: {state}")
        print(f"  Trial #{trial_num} for this state")
        print("-"*60)
        print(f"\n{MotorIntentState.get_description(state)}")
        print(f"Cycles: {self.config.hybrid_cycles} x ({self.config.hybrid_mi_duration}s MI + {self.config.hybrid_rest_duration}s REST)\n")
        
        # Countdown
        print("Countdown to start:")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        # Start signal
        print("\n===== START HYBRID RECORDING =====")
        AudioCues.state_transition(state)
        
        # Prepare filename for base recording
        base_filename = f"eeg_{state}_trial{trial_num:02d}_{self.config.movement_type}"
        full_path = f"new_data/cuantitative/_{self.config.participant_id}_{base_filename}_{time.strftime('%Y%m%d')}.csv"
        
        # Ensure directory exists
        Path("new_data/cuantitative").mkdir(parents=True, exist_ok=True)
        
        # Record with phase tracking
        try:
            from pylsl import StreamInlet, resolve_byprop
            import pandas as pd
            
            print("Looking for EEG stream...")
            streams = resolve_byprop('type', 'EEG', timeout=5)
            
            if not streams:
                print(" No EEG stream found.")
                return False
            
            inlet = StreamInlet(streams[0], max_chunklen=12)
            info = inlet.info()
            
            # Get channel info
            ch = info.desc().child('channels').first_child()
            ch_names = []
            for _ in range(info.channel_count()):
                ch_names.append(ch.child_value('label'))
                ch = ch.next_sibling()
            
            print(f"✓ Connected to stream: {info.name()}")
            print(f"  Channels: {ch_names}")
            print(f"\nRecording hybrid trial (...)\n")
            
            # Storage for samples with labels
            all_samples = []
            timestamps = []
            labels = []
            
            start_time = time.time()
            cycle_duration = self.config.hybrid_mi_duration + self.config.hybrid_rest_duration
            
            for cycle in range(self.config.hybrid_cycles):
                cycle_start = time.time()
                
                # ===== MOTOR IMAGERY PHASE =====
                print(f"\n[Cycle {cycle+1}/{self.config.hybrid_cycles}]")
                print(f">>> MOTOR IMAGERY ACTIVE - {self.config.hybrid_mi_duration}s <<<")
                AudioCues.phase_transition("MOTOR IMAGERY")
                
                mi_phase_start = time.time()
                while time.time() - mi_phase_start < self.config.hybrid_mi_duration:
                    sample, timestamp = inlet.pull_sample(timeout=0.1)
                    if sample:
                        all_samples.append(sample)
                        timestamps.append(timestamp)
                        labels.append('MI') # NEW LABEL
                
                # ===== REST PHASE =====
                print(f"\n>>> REST PERIOD - {self.config.hybrid_rest_duration}s <<<")
                AudioCues.phase_transition("REST")
                
                rest_phase_start = time.time()
                while time.time() - rest_phase_start < self.config.hybrid_rest_duration:
                    sample, timestamp = inlet.pull_sample(timeout=0.1)
                    if sample:
                        all_samples.append(sample)
                        timestamps.append(timestamp)
                        labels.append('REST') #NEW LABEL
            
            # Create DataFrame with labels
            df = pd.DataFrame(all_samples, columns=ch_names)
            df['timestamps'] = timestamps
            df['label'] = labels
            
            # Save to CSV
            df.to_csv(full_path, index=False)
            
            print("\n********************** HYBRID TRIAL COMPLETE **********************")
            AudioCues.recording_complete()
            
            # Save metadata -> useful for analyisis and detailed description.
            self.session_metadata.append({
                'trial': self.current_trial,
                'state': state,
                'trial_num_for_state': trial_num,
                'duration': f"{self.config.hybrid_cycles} cycles",
                'mi_duration': self.config.hybrid_mi_duration,
                'rest_duration': self.config.hybrid_rest_duration,
                'cycles': self.config.hybrid_cycles,
                'filename': full_path,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'samples_collected': len(all_samples),
                'mi_samples': labels.count('MI'),
                'rest_samples': labels.count('REST')
            })
            
            print(f"\n✓ Saved: {full_path}")
            print(f"  Total samples: {len(all_samples)}")
            print(f"  MI samples: {labels.count('MI')} | REST samples: {labels.count('REST')}")
            
            return True
            
        except Exception as e:
            print(f"\nERROR during recording: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_trial(self, trial_info):
        """Execute a single trial (dispatches to hybrid or standard recording)"""
        state = trial_info['state']
        
        # Check if this is a hybrid trial
        if state == MotorIntentState.MOTOR_IMAGERY_HYBRID:
            return self.run_hybrid_trial(trial_info)
        
        # Standard trial execution
        trial_num = trial_info['trial_num']
        duration = trial_info['duration']
        
        self.current_trial += 1
        total_trials = self.config.get_total_trials()
        
        print("\n" + "-"*60)
        print(f"  TRIAL {self.current_trial}/{total_trials}")
        print(f"  State: {state}")
        print(f"  Trial #{trial_num} for this state")
        print("-"*60)
        print(f"\n{MotorIntentState.get_description(state)}")
        print(f"Duration: {duration} seconds\n")
        
        # Countdown
        print("Countdown to start:")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        # Start signal
        print("\n===== START NOW =====\n")
        AudioCues.state_transition(state)
        
        # Record EEG data
        filename = f"eeg_{state}_trial{trial_num:02d}_{self.config.movement_type}"
        self.recorder = EEGRecorder(
            duration=duration,
            filename=filename,
            r_id=self.config.participant_id
        )
        
        # Note: The stream must already be running
        # start recording with visual feedback
        print(f"Recording for {duration} seconds...")
        
        start_time = time.time()
        self.recorder.recording_start_time = start_time
        self.recorder.is_recording = True
        
        try:
            # Use muselsl to record
            from muselsl import record
            
            record(
                duration=duration,
                filename=self.recorder.filename
            )
            
            self.recorder.is_recording = False
            
            # End signal
            print("\n**********************  TRIAL COMPLETE **********************")
            AudioCues.recording_complete()
            
            # Save metadata
            self.session_metadata.append({
                'trial': self.current_trial,
                'state': state,
                'trial_num_for_state': trial_num,
                'duration': duration,
                'filename': self.recorder.filename,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except Exception as e:
            print(f"\n========= ERROR during recording: {e}=========")
            print("run muselsl stream")
            return False
        
        return True
    
    def inter_trial_rest(self):
        """Rest period between trials"""
        if self.current_trial < self.config.get_total_trials():
            print(f"\n⏸  Rest for {self.config.rest_between_trials} seconds...")
            print("Relax and prepare for the next trial.\n")
            time.sleep(self.config.rest_between_trials)
    
    def save_session_metadata(self):
        """Save session metadata to CSV"""
        metadata_filename = f"new_data/cualitative/session_metadata_{self.config.participant_id}_{self.config.session_name}_{time.strftime('%Y%m%d')}.csv"
        
        Path("new_data/cualitative").mkdir(parents=True, exist_ok=True)
        
        with open(metadata_filename, 'w', newline='', encoding='utf-8') as f:
            if self.session_metadata:
                fieldnames = self.session_metadata[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.session_metadata)
        
        print(f"\n Session metadata saved at: {metadata_filename}")
    
    def run_session(self):
        """Execute the complete data acquisition session"""
        print("\n" + "="*60)
        print(" MOTOR INTENT EEG DATA ACQUISITION")
        print("="*60)
        
        # 1. Pre-session survey
        self.conduct_pre_session_survey()
        
        # 2. Generate trial sequence
        self.generate_trial_sequence()
        
        # 3. Display session info
        self.display_session_info()
        
        # 4. Session start signal
        AudioCues.session_start()
        
        # 5. Run all trials
        for trial_info in self.trial_sequence:
            success = self.run_trial(trial_info)
            if not success:
                print("\n⚠️  Trial failed. Do you want to continue? (y/n)")
                if input().lower() != 'y':
                    break
            
            # Rest between trials
            self.inter_trial_rest()
        
        # 6. Session end
        AudioCues.session_end()
        print("\n" + "="*60)
        print("  SESSION COMPLETED!")
        print("="*60)
        print(f"\nTotal trials completed: {len(self.session_metadata)}/{self.config.get_total_trials()}")

        # Post-session survey
        self.conduct_post_session_survey()
        
        # 7. Save metadata
        self.save_session_metadata()
        
        print("=" * 60)
        print("\nAll data saved SUCCESSFULLY")
       


# ============================================
# INTERACTIVE CONFIGURATION
# ============================================

def configure_session() -> SessionConfig:
    """Interactive session configuration"""
    config = SessionConfig()
    
    print("\n" + "="*60)
    print("  SESSION CONFIGURATION")
    print("="*60)
    
    # Participant ID
    p_id = input(f"\nParticipant ID (default: {config.participant_id}): ").strip()
    if p_id:
        config.participant_id = p_id
    
    # Session name
    session = input(f"Session name (default: {config.session_name}): ").strip()
    if session:
        config.session_name = session
    
    # Trial duration
    duration = input(f"Trial duration in seconds (default: {config.trial_duration}): ").strip()
    if duration.isdigit():
        config.trial_duration = int(duration)
    
    # Trials per state
    trials = input(f"Trials per state (default: {config.trials_per_state}): ").strip()
    if trials.isdigit():
        config.trials_per_state = int(trials)
    
    # Movement type
    movement = input(f"Movement type (default: {config.movement_type}): ").strip()
    if movement:
        config.movement_type = movement
    
    # Rest between trials
    rest = input(f"Rest between trials in seconds (default: {config.rest_between_trials}): ").strip()
    if rest.isdigit():
        config.rest_between_trials = int(rest)
    
    return config


# ============================================
# STREAM VERIFICATION
# ============================================

def verify_stream():
    """Verify that muselsl stream is running"""
    print("\n" + "="*60)
    print("  CHECKING FOR EEG STREAM")
    print("="*60)
    print("\nIMPORTANT: 'muselsl stream' should be running")
    print("   in another terminal window.\n")
    print("Checking for LSL stream...")
    
    try:
        from pylsl import resolve_streams
        
        # Look for any EEG stream
        streams = resolve_streams(wait_time=5)
        
        if not streams:
            print("\n No LSL stream found.")
            print("\nTo start the stream, run 'muselsl stream' in another terminal.")
            print("\n Then, run this script again.")
            return False
        
        print(f"\nFound {len(streams)} streams:")
        for s in streams:
            print(f"  - {s.name()} ({s.type()}): {s.channel_count()} channels")
        
        return True
        
    except ImportError:
        print("\n pylsl not available, skipping stream check")
        print("Assuming stream is running...")
        return True
    except Exception as e:
        print(f"\n Error checking stream: {e}")
        print("Proceeding anyway...")
        return True


# ============================================
# MAIN FUNCTION
# ============================================

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("  MOTOR INTENT EEG DATA ACQUISITION SYSTEM")
    print("  Muse 2 Headset - Research Edition")
    print("="*70)
    
    # Check for stream
    if not verify_stream():
        print("\n Stream not detected.")
        sys.exit(1)
    
    # Configure session
    config = configure_session()
    
    # Create and run session
    acquisition = MotorIntentDataAcquisition(config)
    
    try:
        acquisition.run_session()
    except KeyboardInterrupt:
        print("\n\n Session interrupted by user. ")
        print(f"Trials completed: {len(acquisition.session_metadata)}")
        if acquisition.session_metadata:
            acquisition.save_session_metadata()
    except Exception as e:
        print(f"\n Error during session: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
