"""
written by Bini Vázquez.

Manual Motor Imagery Labeling System for EEG Data Acquisition with Muse 2 Headset.
Real-time keyboard-based labeling for more accurate and balanced datasets.

Features:
  - Real-time keyboard input detection
  - Manual labeling of MI/REST/TRANSITION states
  - Live visual feedback and statistics
  - Seamless integration with existing EEGRecorder
  - Export labeled data ready for ML training

Keyboard Controls:
  - 'M' or 'm': Motor Imagery (MI) label
  - 'R' or 'r': Rest label
  - 'T' or 't': Transition/Uncertain label
  - 'Q' or 'q': Stop recording and save
  - 'S' or 's': Show current statistics

IMPORTANT: Must have 'muselsl stream' running in another terminal
"""

import sys
import time
import csv
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter
from pylsl import resolve_streams
from pylsl import StreamInlet, resolve_byprop

# Import existing classes
sys.path.append(str(Path(__file__).parent))
from eeg_recording import EEGRecorder

# create GLOBAL file prefix
DATA_ROOT = Path("new_data/manual_labeling/cuantitative")
DATA_ROOT.mkdir(parents=True, exist_ok=True)



# Platform-specific keyboard input handling // in case @lalo or @dani are using this piece of code on Windows.
try:
    import msvcrt  # Windows
    PLATFORM = 'windows'
except ImportError:
    try:
        import tty, termios  # Unix/Mac
        PLATFORM = 'unix'
    except ImportError:
        PLATFORM = 'unknown'


# *************** KEYBOARD INPUT HANDLER *************** #

class KeyboardInputHandler:
    """
    Cross-platform keyboard input detection for real-time labeling.
    Non-blocking input detection that works during EEG recording.
    Returns pressed keys or default "REST" if no key pressed.
    """
    
    def __init__(self):
        self.platform = PLATFORM
        self.old_settings = None
        
    def setup_terminal(self):
        """Setup terminal for non-blocking input (Unix/Mac only)"""
        if self.platform == 'unix':
            import sys, tty, termios # in func imports for innecessary platforms
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
    
    def restore_terminal(self):
        """Restore terminal to original settings (Unix/Mac only)"""
        if self.platform == 'unix' and self.old_settings:
            import sys, termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
    
    def get_key(self, timeout=0.1):
        """
        Get a single keypress without blocking (non-blocking with timeout).
        
        Returns:
            str: The pressed key or None if no key pressed
        """
        if self.platform == 'windows':
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
            return None
            
        elif self.platform == 'unix':
            import sys, select
            dr, dw, de = select.select([sys.stdin], [], [], timeout)
            if dr:
                return sys.stdin.read(1)
            return None
        
        else:
            # Fallback: blocking input with prompt
            print("Press key + ENTER: ")
            return input().strip()[:1] if input().strip() else None


# *************** MANUAL LABELING SESSION *************** #

class ManualLabelingSession:
    """
    Real-time manual labeling session with keyboard input.
    Records EEG while user labels states via keyboard.
    """
    
    # Label mappings
    LABELS = {
        'M': 'MI',      # Motor Imagery
        'R': 'REST',    # Rest
        'T': 'TRANS',   # uncertain/Transition
        'Q': 'QUIT',    # stop 
        'S': 'STATS'    # show stats
    }
    
    # took this piece from previous data acquisition scripts
    def __init__(self, participant_id="000", session_name="manual_labeling", 
                 movement_type="right_hand_fist"):
        """
        Initialize manual labeling session.
        
        args:
            participant_id: Participant identifier --> 001 is me.
            session_name: Name for this session
            movement_type: Type of motor task being performed

        """
        self.participant_id = participant_id
        self.session_name = session_name
        self.movement_type = movement_type
        
        # Session state
        self.is_recording = False
        self.start_time = None
        self.current_label = 'REST'  # Default label
        
        # Data storage
        self.samples = []
        self.timestamps = []
        self.labels = []
        self.label_changes = []  # Track when labels change
        
        # Keyboard handler
        self.keyboard = KeyboardInputHandler()
        
        # Threading
        self.recording_thread = None
        self.input_thread = None
        self.stop_flag = threading.Event()
    
    def display_instructions(self):
        """Shows keyboard controls to user"""

        print("\n" + "="*60)
        print("  MANUAL LABELING - KEYBOARD CONTROLS")
        print("="*60)
        print("\nPress these keys DURING recording to label:")
        print("  [M] - Motor Imagery (MI)")
        print("  [R] - Rest")
        print("  [T] - Transition/Uncertain")
        print("  [S] - Show current statistics")
        print("  [Q] - Stop recording and save")
        print("\n" + "="*60)
        print(f"\nParticipant: {self.participant_id}")
        print(f"Session: {self.session_name}")
        print(f"Movement: {self.movement_type}")
        print("="*60 + "\n")
    
    def get_label_statistics(self):
        """Calculate current label distribution. Allows to 'balance' the dataset in real time."""
        if not self.labels:
            return {}
        
        counter = Counter(self.labels)
        total = len(self.labels)
        
        stats = {}
        for label, count in counter.items():
            percentage = (count / total) * 100
            stats[label] = {
                'count': count,
                'percentage': percentage
            }
        
        return stats
    
    def display_statistics(self):
        """Show current session statistics"""
        stats = self.get_label_statistics()
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "-"*50)
        print(f"  SESSION STATISTICS (t-elapsed: {elapsed:.1f}s)")
        print("-"*50)
        print(f"Total samples: {len(self.samples)}")
        print(f"Current label: {self.current_label}")
        print(f"\nLabel distribution:")
        
        for label, data in stats.items():
            print(f"  {label:8s}: {data['count']:5d} samples ({data['percentage']:5.1f}%)")
        
        print(f"\nLabel changes: {len(self.label_changes)}")
        print("-"*50 + "\n")
    
    def display_live_feedback(self):
        """Show live feedback during recording"""
        elapsed = time.time() - self.start_time
        sample_count = len(self.samples)
        
        # clear line and show status
        print(f"\r  REC: {elapsed:.1f}s | Samples: {sample_count} | Label: [{self.current_label}]", 
              end='', flush=True)
    
    def handle_keyboard_input(self):
        """Thread function to handle keyboard input during recording"""
        self.keyboard.setup_terminal()
        
        try:
            while not self.stop_flag.is_set():
                key = self.keyboard.get_key(timeout=0.1)
                
                if key:
                    key_upper = key.upper()
                    
                    if key_upper in self.LABELS:
                        label_action = self.LABELS[key_upper]
                        
                        if label_action == 'QUIT':
                            print("\n\n[User requested stop]")
                            self.stop_flag.set()
                            break
                        
                        elif label_action == 'STATS':
                            print()  # New line before stats
                            self.display_statistics()
                        
                        else:
                            # Change current label
                            if label_action != self.current_label:
                                old_label = self.current_label
                                self.current_label = label_action
                                
                                # Record label change
                                self.label_changes.append({
                                    'time': time.time() - self.start_time,
                                    'from': old_label,
                                    'to': self.current_label,
                                    'sample_index': len(self.samples)
                                })
                                
                                print(f"\n>>> Label changed: FROM {old_label} TO {self.current_label}")
        
        finally:
            self.keyboard.restore_terminal()
    
    def record_eeg_stream(self):
        """Thread function to record EEG data from LSL stream"""
        try:
            
            print("\nLooking for EEG stream...")
            streams = resolve_byprop('type', 'EEG', timeout=5)
            
            if not streams:
                print("No muse stream found.")
                self.stop_flag.set()
                return
            
            inlet = StreamInlet(streams[0], max_chunklen=12)
            info = inlet.info()
            
            # Get channel info
            ch = info.desc().child('channels').first_child()
            self.ch_names = []
            for _ in range(info.channel_count()):
                self.ch_names.append(ch.child_value('label'))
                ch = ch.next_sibling()
            
            print(f"SUCCESS. Connected to: {info.name()}")
            print(f"Channels: {self.ch_names}")
            print(f"SR: {info.nominal_srate()} Hz")
            print("\n>>> Recording started - Use keyboard to label!\n")
            
            # Record samples using pul_chunk for efficiency
            # Muse 2 specs: 256 Hz sampling rate
            # With timeout=0.0: non-blocking, returns immediately with available data
            # With max_samples=256: retrieves up to 1 second of buffered data per call
            # This is optimal because:
            #   - 256 samples = exactly 1 second at 256 Hz (intuitive chunk size)
            #   - Non-blocking prevents delays in keyboard input detection
            #   - Reduces function call overhead vs pull_sample()
            #   - Less likely to miss samples during brief processing delays
            
            feedback_counter = 0
            while not self.stop_flag.is_set():
                # Pull chunk of samples (more efficient than single samples)
                samples_chunk, timestamps_chunk = inlet.pull_chunk(timeout=0.0, max_samples=256)
                
                if timestamps_chunk:  # If we got any samples
                    # Extend lists with all samples from chunk
                    self.samples.extend(samples_chunk) # extend() is append() but cute.
                    self.timestamps.extend(timestamps_chunk)
                    # Apply current label to all samples in this chunk
                    self.labels.extend([self.current_label] * len(timestamps_chunk))
                    
                    # Show live feedback every 50 ish samples (more appropriate for chunks)
                    feedback_counter += len(timestamps_chunk)
                    if feedback_counter >= 50:
                        self.display_live_feedback()
                        feedback_counter = 0
                else:
                    # No data available, small sleep to prevent CPU impatient burn
                    time.sleep(0.01)
        
        except Exception as e:
            print(f"\n ERROR during recording, CHECK: {e}")
            import traceback # in function for cleaner logs.
            traceback.print_exc()
            self.stop_flag.set()
    
    def save_labeled_data(self):
        """Save labeled EEG data to CSV"""
        if not self.samples:
            print("\n NO DATA to save.")
            return None
        
        # Prepare filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_ROOT}_{self.participant_id}_manual_labeled_{self.session_name}_{self.movement_type}_{timestamp}.csv"
        
        # Ensure directory exists AGAIN.
        Path(DATA_ROOT).mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame and save
        try:
            
            df = pd.DataFrame(self.samples, columns=self.ch_names)
            df['timestamps'] = self.timestamps
            df['label'] = self.labels
            
            # Add relative time column
            if self.timestamps:
                first_timestamp = self.timestamps[0]
                df['relative_time'] = [t - first_timestamp for t in self.timestamps]
            
            df.to_csv(filename, index=False)
            
            print(f"\n✅ Data saved: {filename}")
            print(f"   Total samples: {len(self.samples)}")
            
            # Show final statistics
            self.display_statistics()
            
            return filename
            
        except Exception as e:
            print(f"\n FATAL ERROR: data could not be saved: {e}")
            return None
    
    def save_session_metadata(self):
        """Save session metadata and label changes"""
        if not self.label_changes:
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        metadata_file = f"new_data/cualitative/manual_labeling_metadata_{self.participant_id}_{self.session_name}_{timestamp}.csv"
        
        Path("new_data/cualitative").mkdir(parents=True, exist_ok=True)
        
        try:
            with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['time', 'from', 'to', 'sample_index'])
                writer.writeheader()
                writer.writerows(self.label_changes)
            
            print(f"metadata saved: {metadata_file}") # claude code rec, could be useful for later analysis.
            
        except Exception as e:
            print(f"(NOT SO) FATAL ERROR to save metadata: {e}")
    
    def start_session(self, max_duration=None):
        """
        Start manual labeling session.
        THE GOAT FUNCCCCCCTIONNNN....
        
        Args:
            max_duration: Maximum duration in seconds (None = unlimited)
        """
        self.display_instructions()
        
        input("Press [ENTER] when ready to start recording...")
        
        # Initialize
        self.start_time = time.time()
        self.is_recording = True
        self.stop_flag.clear()
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_eeg_stream, daemon=True)
        self.recording_thread.start()
        
        # Start keyboard input thread
        self.input_thread = threading.Thread(target=self.handle_keyboard_input, daemon=True)
        self.input_thread.start()
        
        # Monitor session
        try:
            while not self.stop_flag.is_set():
                time.sleep(0.1) #10 checks/second POR CPUs sake.
                
                # Check max duration
                if max_duration and (time.time() - self.start_time) >= max_duration:
                    print(f"\n\nEND or MAX DURATION ({max_duration}s) reached.")
                    self.stop_flag.set()
                    break
        
        except KeyboardInterrupt:
            print("\n\"User interrupted session. BYE.")
            self.stop_flag.set()
        
        # Wait for threads to finish
        print("\nStopping recording...")
        self.recording_thread.join(timeout=2)
        self.input_thread.join(timeout=2)
        
        self.is_recording = False
        
        print("\n" + "="*60)
        print("  RECORDING COMPLETED")
        print("="*60)
        
        # Save data
        self.save_labeled_data()
        self.save_session_metadata()
        
        print("\nSession COMPLETED successfully!\n")


# *************** INTERACTIVE SESSION CONFIG *************** #

def configure_manual_session():
    """Interactive configuration for manual labeling session"""
    print("\n" + "="*60)
    print("  MANUAL LABELING SESSION - CONFIGURATION")
    print("="*60)
    
    participant_id = input("\nParticipant ID: ").strip() or "000" # LOVE THIS SYNTAX!
    session_name = input("Session name (default: random_test): ").strip() or "random_test"
    movement_type = input("Movement type (default: right_hand_fist): ").strip() or "right_hand_fist"
    
    max_duration_input = input("Max duration in seconds (default: unlimited): ").strip()
    max_duration = int(max_duration_input) if max_duration_input.isdigit() else None
    
    return {
        'participant_id': participant_id,
        'session_name': session_name,
        'movement_type': movement_type,
        'max_duration': max_duration
    }


# *************** STREAM VERIFICATION *************** #

def verify_stream():
    """Verify that muselsl stream is running"""
    print("\n" + "="*60)
    print("  CHECKING FOR EEG STREAM")
    print("="*60)
    print("\nis 'muselsl stream' must be running in another terminal? IGNORE IF APPLIES...\n")
    
    try:
        
        print("Checking for LSL stream...")
        streams = resolve_streams(wait_time=5)
        
        if not streams:
            print("\n No LSL stream found.")
            print("\nTo start the stream:")
            print("  1. Open another terminal")
            print("  2. Run: muselsl stream")
            print("  3. Wait for connection")
            print("  4. Run this script again\n")
            return False
        
        print(f"\n FOUND {len(streams)} stream(s):")
        for s in streams:
            print(f"   • {s.name()} ({s.type()}): {s.channel_count()} channels")
        
        return True
        
    except ImportError:
        print("\npylsl not installed. NOOB:")
        print("   pip install pylsl")
        return False
    except Exception as e:
        print(f"\n FATAL ERROR checking stream: {e}")
        return False


# *************** MAIN EXECUTION *************** #

def main():
    """Main function to run manual labeling session"""
    print("\n" + "="*60)
    print("  MANUAL MOTOR IMAGERY LABELING SYSTEM")
    print("="*60)
    
    # Verify stream
    if not verify_stream():
        return
    
    # Configure session
    config = configure_manual_session()
    
    # Create and run session
    session = ManualLabelingSession(
        participant_id=config['participant_id'],
        session_name=config['session_name'],
        movement_type=config['movement_type']
    )
    
    try:
        session.start_session(max_duration=config['max_duration'])
    except Exception as e:
        print(f"\n FATAL ERROR in session: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() # run this script directly for manual labeling.
