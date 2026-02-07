"""
Captura de Artefactos Faciales - Etiquetado Manual
===================================================
Sistema simple de terminal para capturar datos de artefactos faciales.
Audio cues + etiquetado manual por teclado.

Escrito por Bini Vázquez para investigación con adultos mayores.

Características:
  - Audio cues en español para guiar al participante
  - Etiquetado manual por teclado durante la grabación
  - Feedback en vivo en terminal
  - Sin GUI - solo terminal
  - Auto-guardado continuo

Controles de Teclado:
  [D] - Parpadeo Derecho
  [I] - Parpadeo Izquierdo  
  [C] - Levantar Cejas
  [R] - Reposo
  [S] - Mostrar estadísticas
  [Q] - Detener y guardar

IMPORTANTE: Debe tener 'muselsl stream -a 00:55:da:b5:b3:1e' corriendo en otra terminal
"""

import sys
import time
import csv
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter
from pylsl import resolve_streams, StreamInlet, resolve_byprop

# Audio
try:
    import pyttsx3
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  pyttsx3 no disponible. Instalar con: pip install pyttsx3")

# =========================
# CONFIG
# =========================
MUSE_MAC = "00:55:da:b5:b3:1e"
DATA_ROOT = Path("facial_artifact_datasets")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# Keyboard handling
try:
    import msvcrt  # Windows
    PLATFORM = 'windows'
except ImportError:
    try:
        import tty, termios  # Unix/Mac
        PLATFORM = 'unix'
    except ImportError:
        PLATFORM = 'unknown'

# =========================
# Audio Manager
# =========================
class AudioCueManager:
    """Maneja audio cues en español"""
    
    def __init__(self):
        self.enabled = AUDIO_AVAILABLE
        self.engine = None
        self.lock = threading.Lock()
        
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 130)
                self.engine.setProperty('volume', 1.0)
                
                # Buscar voz en español
                voices = self.engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        voice_name = voice.name.lower()
                        voice_lang = getattr(voice, 'languages', [])
                        if 'spanish' in voice_name or 'es' in str(voice_lang) or 'español' in voice_name:
                            self.engine.setProperty('voice', voice.id)
                            print("🔊 Voz en español configurada")
                            break
            except Exception as e:
                print(f"⚠️  Error audio: {e}")
                self.enabled = False
    
    def speak(self, text: str):
        """Hablar texto de forma asíncrona"""
        if not self.enabled:
            print(f"[AUDIO] {text}")
            return
        
        def _speak():
            with self.lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"⚠️  Error audio: {e}")
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def cue_action(self, action: str):
        """Audio cue para cada acción"""
        messages = {
            "PARPADEO_DERECHO": "Parpadee con el ojo derecho varias veces",
            "PARPADEO_IZQUIERDO": "Parpadee con el ojo izquierdo varias veces",
            "LEVANTAR_CEJAS": "Levante las cejas hacia arriba y abajo",
            "REPOSO": "Reposo. Relájese"
        }
        msg = messages.get(action, action)
        self.speak(msg)

# =========================
# Keyboard Handler
# =========================
class KeyboardInputHandler:
    """Captura de teclado no-bloqueante"""
    
    def __init__(self):
        self.platform = PLATFORM
        self.old_settings = None
        
    def setup_terminal(self):
        """Setup para input no-bloqueante (Unix/Mac)"""
        if self.platform == 'unix':
            import sys, tty, termios
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
    
    def restore_terminal(self):
        """Restaurar terminal (Unix/Mac)"""
        if self.platform == 'unix' and self.old_settings:
            import sys, termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
    
    def get_key(self, timeout=0.1):
        """
        Obtener tecla sin bloquear
        Returns: tecla presionada o None
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
            print("Presione tecla + ENTER: ")
            inp = input().strip()
            return inp[:1] if inp else None

# =========================
# Sesión de Captura
# =========================
class FacialArtifactSession:
    """Sesión de captura de artefactos faciales con etiquetado manual"""
    
    LABELS = {
        'D': 'PARPADEO_DERECHO',
        'I': 'PARPADEO_IZQUIERDO',
        'C': 'LEVANTAR_CEJAS',
        'R': 'REPOSO',
        'Q': 'QUIT',
        'S': 'STATS'
    }
    
    def __init__(self, participant_id="000", session_name="facial_artifacts"):
        """
        Inicializar sesión de captura
        
        Args:
            participant_id: ID del participante
            session_name: Nombre de la sesión
        """
        self.participant_id = participant_id
        self.session_name = session_name
        
        # Estado de la sesión
        self.is_recording = False
        self.start_time = None
        self.current_label = 'REPOSO'
        
        # Almacenamiento de datos
        self.samples = []
        self.timestamps = []
        self.labels = []
        self.label_changes = []
        
        # Audio
        self.audio = AudioCueManager()
        
        # Keyboard
        self.keyboard = KeyboardInputHandler()
        
        # Threading
        self.recording_thread = None
        self.input_thread = None
        self.stop_flag = threading.Event()
    
    def display_instructions(self):
        """Mostrar instrucciones"""
        print("\n" + "="*70)
        print("  CAPTURA DE ARTEFACTOS FACIALES - ETIQUETADO MANUAL")
        print("="*70)
        print("\n📋 CONTROLES DE TECLADO (presione durante la grabación):")
        print("\n  [D] - Parpadeo Ojo Derecho")
        print("  [I] - Parpadeo Ojo Izquierdo")
        print("  [C] - Levantar Cejas")
        print("  [R] - Reposo")
        print("  [S] - Mostrar Estadísticas")
        print("  [Q] - Detener y Guardar")
        print("\n" + "="*70)
        print(f"\n👤 Participante: {self.participant_id}")
        print(f"📝 Sesión: {self.session_name}")
        print("="*70 + "\n")
    
    def get_label_statistics(self):
        """Calcular distribución de etiquetas"""
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
        """Mostrar estadísticas de la sesión"""
        stats = self.get_label_statistics()
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "-"*60)
        print(f"  ESTADÍSTICAS (tiempo transcurrido: {elapsed:.1f}s)")
        print("-"*60)
        print(f"Total de muestras: {len(self.samples)}")
        print(f"Etiqueta actual: {self.current_label}")
        print(f"\nDistribución de etiquetas:")
        
        for label, data in stats.items():
            print(f"  {label:20s}: {data['count']:5d} muestras ({data['percentage']:5.1f}%)")
        
        print(f"\nCambios de etiqueta: {len(self.label_changes)}")
        print("-"*60 + "\n")
    
    def display_live_feedback(self):
        """Feedback en vivo durante la grabación"""
        elapsed = time.time() - self.start_time
        sample_count = len(self.samples)
        
        print(f"\r  ⏺  GRABANDO: {elapsed:.1f}s | Muestras: {sample_count} | Etiqueta: [{self.current_label}]", 
              end='', flush=True)
    
    def handle_keyboard_input(self):
        """Thread para manejar input de teclado"""
        self.keyboard.setup_terminal()
        
        try:
            while not self.stop_flag.is_set():
                key = self.keyboard.get_key(timeout=0.1)
                
                if key:
                    key_upper = key.upper()
                    
                    if key_upper in self.LABELS:
                        label_action = self.LABELS[key_upper]
                        
                        if label_action == 'QUIT':
                            print("\n\n[Usuario solicitó detener]")
                            self.stop_flag.set()
                            break
                        
                        elif label_action == 'STATS':
                            print()
                            self.display_statistics()
                        
                        else:
                            # Cambiar etiqueta actual
                            if label_action != self.current_label:
                                old_label = self.current_label
                                self.current_label = label_action
                                
                                # Registrar cambio
                                self.label_changes.append({
                                    'time': time.time() - self.start_time,
                                    'from': old_label,
                                    'to': self.current_label,
                                    'sample_index': len(self.samples)
                                })
                                
                                # Audio cue
                                self.audio.cue_action(self.current_label)
                                
                                print(f"\n>>> Cambio: {old_label} → {self.current_label}")
        
        finally:
            self.keyboard.restore_terminal()
    
    def record_eeg_stream(self):
        """Thread para grabar datos EEG del stream LSL"""
        try:
            print("\n🔍 Buscando stream EEG...")
            streams = resolve_byprop('type', 'EEG', timeout=10)
            
            if not streams:
                print("❌ No se encontró stream Muse.")
                print("\n💡 Asegúrate de ejecutar en otra terminal:")
                print(f"   muselsl stream -a {MUSE_MAC}")
                self.stop_flag.set()
                return
            
            inlet = StreamInlet(streams[0], max_chunklen=12)
            info = inlet.info()
            
            # Obtener nombres de canales
            ch = info.desc().child('channels').first_child()
            self.ch_names = []
            for _ in range(info.channel_count()):
                self.ch_names.append(ch.child_value('label'))
                ch = ch.next_sibling()
            
            print(f"✅ Conectado a: {info.name()}")
            print(f"📊 Canales: {', '.join(self.ch_names)}")
            print(f"🔄 Frecuencia: {info.nominal_srate()} Hz")
            print("\n>>> ¡Grabación iniciada! Use el teclado para etiquetar.\n")
            
            # Registrar muestras
            feedback_counter = 0
            while not self.stop_flag.is_set():
                samples_chunk, timestamps_chunk = inlet.pull_chunk(timeout=0.0, max_samples=256)
                
                if timestamps_chunk:
                    self.samples.extend(samples_chunk)
                    self.timestamps.extend(timestamps_chunk)
                    self.labels.extend([self.current_label] * len(timestamps_chunk))
                    
                    feedback_counter += len(timestamps_chunk)
                    if feedback_counter >= 50:
                        self.display_live_feedback()
                        feedback_counter = 0
                else:
                    time.sleep(0.01)
        
        except Exception as e:
            print(f"\n❌ ERROR durante grabación: {e}")
            import traceback
            traceback.print_exc()
            self.stop_flag.set()
    
    def save_labeled_data(self):
        """Guardar datos etiquetados a CSV"""
        if not self.samples:
            print("\n⚠️  No hay datos para guardar.")
            return None
        
        # Nombre de archivo
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_dir = DATA_ROOT / f"FACIAL_{self.participant_id}_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        filename = session_dir / "labeled_data.csv"
        
        try:
            df = pd.DataFrame(self.samples, columns=self.ch_names)
            df['timestamp'] = self.timestamps
            df['label'] = self.labels
            
            # Tiempo relativo
            if self.timestamps:
                first_timestamp = self.timestamps[0]
                df['relative_time'] = [t - first_timestamp for t in self.timestamps]
            
            df.to_csv(filename, index=False)
            
            print(f"\n✅ Datos guardados: {filename}")
            print(f"   Total de muestras: {len(self.samples)}")
            
            # Estadísticas finales
            self.display_statistics()
            
            return filename
            
        except Exception as e:
            print(f"\n❌ ERROR al guardar datos: {e}")
            return None
    
    def save_session_metadata(self):
        """Guardar metadata de la sesión"""
        if not self.label_changes:
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_dir = DATA_ROOT / f"FACIAL_{self.participant_id}_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = session_dir / "label_changes.csv"
        
        try:
            with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['time', 'from', 'to', 'sample_index'])
                writer.writeheader()
                writer.writerows(self.label_changes)
            
            print(f"📝 Metadata guardada: {metadata_file}")
            
            # Guardar también meta.json
            import json
            meta_file = session_dir / "meta.json"
            meta = {
                "participant_id": self.participant_id,
                "session_name": self.session_name,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
                "duration_seconds": time.time() - self.start_time,
                "total_samples": len(self.samples),
                "channels": self.ch_names,
                "label_counts": self.get_label_statistics(),
                "label_changes_count": len(self.label_changes)
            }
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Meta información: {meta_file}")
            
        except Exception as e:
            print(f"⚠️  Error al guardar metadata: {e}")
    
    def start_session(self, max_duration=None):
        """
        Iniciar sesión de captura
        
        Args:
            max_duration: Duración máxima en segundos (None = ilimitado)
        """
        self.display_instructions()
        
        # Audio inicial
        self.audio.speak("Bienvenido a la sesión de captura de artefactos faciales")
        
        input("\n▶️  Presione [ENTER] cuando esté listo para comenzar...")
        
        # Inicializar
        self.start_time = time.time()
        self.is_recording = True
        self.stop_flag.clear()
        
        self.audio.speak("Iniciando grabación")
        
        # Iniciar threads
        self.recording_thread = threading.Thread(target=self.record_eeg_stream, daemon=True)
        self.recording_thread.start()
        
        self.input_thread = threading.Thread(target=self.handle_keyboard_input, daemon=True)
        self.input_thread.start()
        
        # Monitorear sesión
        try:
            while not self.stop_flag.is_set():
                time.sleep(0.1)
                
                # Verificar duración máxima
                if max_duration and (time.time() - self.start_time) >= max_duration:
                    print(f"\n\n⏱️  Duración máxima ({max_duration}s) alcanzada.")
                    self.stop_flag.set()
                    break
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Sesión interrumpida por el usuario.")
            self.stop_flag.set()
        
        # Esperar a que terminen los threads
        print("\n⏹️  Deteniendo grabación...")
        self.recording_thread.join(timeout=2)
        self.input_thread.join(timeout=2)
        
        self.is_recording = False
        
        print("\n" + "="*70)
        print("  GRABACIÓN COMPLETADA")
        print("="*70)
        
        self.audio.speak("Sesión completada. Guardando datos.")
        
        # Guardar datos
        self.save_labeled_data()
        self.save_session_metadata()
        
        print("\n✅ ¡Sesión completada exitosamente!\n")

# =========================
# Verificación de Stream
# =========================
def verify_stream():
    """Verificar que el stream LSL esté corriendo"""
    print("\n" + "="*70)
    print("  VERIFICANDO STREAM EEG")
    print("="*70)
    
    try:
        print("\n🔍 Buscando stream LSL...")
        streams = resolve_streams(wait_time=5)
        
        if not streams:
            print("\n❌ No se encontró stream LSL.")
            print("\n💡 Para iniciar el stream:")
            print("   1. Abra otra terminal")
            print(f"   2. Ejecute: muselsl stream -a {MUSE_MAC}")
            print("   3. Espere la conexión")
            print("   4. Ejecute este script nuevamente\n")
            return False
        
        print(f"\n✅ Se encontraron {len(streams)} stream(s):")
        for s in streams:
            print(f"   • {s.name()} ({s.type()}): {s.channel_count()} canales")
        
        return True
        
    except ImportError:
        print("\n❌ pylsl no instalado.")
        print("   pip install pylsl")
        return False
    except Exception as e:
        print(f"\n❌ Error al verificar stream: {e}")
        return False

# =========================
# Configuración de Sesión
# =========================
def configure_session():
    """Configuración interactiva de la sesión"""
    print("\n" + "="*70)
    print("  CONFIGURACIÓN DE SESIÓN")
    print("="*70)
    
    participant_id = input("\n👤 ID del Participante (ej: AM01 para adulto mayor 01): ").strip() or "000"
    session_name = input("📝 Nombre de sesión (default: facial_artifacts): ").strip() or "facial_artifacts"
    
    max_duration_input = input("⏱️  Duración máxima en segundos (default: ilimitado): ").strip()
    max_duration = int(max_duration_input) if max_duration_input.isdigit() else None
    
    return {
        'participant_id': participant_id,
        'session_name': session_name,
        'max_duration': max_duration
    }

# =========================
# MAIN
# =========================
def main():
    """Función principal"""
    print("\n" + "="*70)
    print("  CAPTURA DE ARTEFACTOS FACIALES - ADULTOS MAYORES")
    print("  Sistema de Etiquetado Manual")
    print("="*70)
    
    # Verificar stream
    if not verify_stream():
        return
    
    # Configurar sesión
    config = configure_session()
    
    # Crear y ejecutar sesión
    session = FacialArtifactSession(
        participant_id=config['participant_id'],
        session_name=config['session_name']
    )
    
    try:
        session.start_session(max_duration=config['max_duration'])
    except Exception as e:
        print(f"\n❌ ERROR en la sesión: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
