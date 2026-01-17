import muselsl as muse
from muselsl import record, list_muses
import time
import subprocess
import signal
import atexit

class EEGRecorder:
    """
    Clase básica para grabación de EEG con Muse 2.
    Para sesiones completas con audio cues y múltiples estados, usar data_compiler_ui.py
    """
    def __init__(self, duration, filename, r_id="000"):
        self.date_str = time.strftime("%Y%m%d")
        self.r_id = r_id 
        self.duration = duration
        self.filename = f"new_data/cuantitative/_{r_id}_{filename}_{self.date_str}.csv"
        self.stream_process = None
        self.recording_start_time = None
        self.is_recording = False
    
    # 1. CONFIRMAR PAIRING CON MUSE
    def confirm_pairing(self):
        paired = muse.list_muses()
        if not paired:
            print(f"NO SE ENCONTRÓ LA MUSE 2.")
            return None
        else:
            mi_muse = paired[0]
            print(f"SE ENCONTRÓ LA MUSE 2: {mi_muse['name']} - {mi_muse['address']}")
            return mi_muse
    
    def start_stream(self):
        """
        Inicia el stream en un proceso separado automáticamente.
        """
        print("\n******** Iniciando Stream Automáticamente ********")
        
        try:
            # Iniciar muselsl stream como proceso en background
            self.stream_process = subprocess.Popen(
                ['muselsl', 'stream'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Registrar cleanup para cuando el programa termine
            atexit.register(self.stop_stream)
            
            print("Esperando a que el stream se establezca...")
            time.sleep(5)  # Dar tiempo suficiente
            print("✅ Stream establecido.\n")
            return True
            
        except Exception as e:
            print(f"❌ Error al iniciar stream: {e}")
            return False
    
    def stop_stream(self):
        """
        Detiene el stream process cuando termine el programa.
        """
        if self.stream_process:
            print("\nDeteniendo stream...")
            self.stream_process.send_signal(signal.SIGINT)
            self.stream_process.wait(timeout=3)
            print("Stream detenido.")
    
    
    def start_recording(self):
        """
        Inicia la grabación de datos EEG.
        
        IMPORTANTE: Debes iniciar el stream manualmente ANTES en una terminal:
            muselsl stream
        
        Luego ejecuta este script para grabar.
        """
        print(f"\n******** Recording Started for {self.duration} seconds ********")
        print("'muselsl stream' debe estar corriendo en otra terminal.")
        print("Buscando el stream LSL...")
        
        # Dar tiempo para detectar el stream
        time.sleep(2)
        
        try:
            # Simplemente llamar record() - asume que el stream ya está corriendo
            print("Grabando...\n")
            record(
                duration=self.duration,
                filename=self.filename
            )
            
            print(f"\nEEG Recording Successfully Saved!")
            print(f"Data saved at: {self.filename}\n")
        except Exception as e:
            print(f"\nError durante la grabación: {e}")
            print("Asegúrate de que 'muselsl stream' esté corriendo en otra terminal.\n")
    
    def recording_timer(self):
        """
        Verifica si la grabación aún está activa basándose en el tiempo transcurrido.
        Returns:
            tuple: (is_active, elapsed_time, remaining_time)
        """
        # Base Case: No hemos iniciado la grabación
        if not self.recording_start_time:
            return (False, 0, 0)
        
        elapsed_time = time.time() - self.recording_start_time # INTEGRAL (?) DELTA T
        remaining_time = max(0, self.duration - elapsed_time) # Clampeaa a 0.
        is_active = elapsed_time < self.duration and self.is_recording
        
        return (is_active, elapsed_time, remaining_time)

    
    def get_recording_progress(self):
        """
        Obtiene el progreso de la grabación como porcentaje.
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        is_active, elapsed, remaining = self.recording_timer()
        if self.duration == 0:
            return 100.0
        progress = (elapsed / self.duration) * 100
        return min(progress, 100.0) # calculamos min para encapsular en el rango 0-100.
    
    def wait_for_recording(self, update_interval=1.0):
        """
        Loop que espera hasta que la grabación termine, 
        mostrando el progreso cada update_interval segundos.
        
        Args:
            update_interval: Tiempo en segundos entre actualizaciones de progreso
        """
        if not self.is_recording:
            print("No hay grabación activa.")
            return
        
        print("\n--- Recording Progress ---")
        while self.is_recording:
            is_active, elapsed, remaining = self.recording_timer()
            if not is_active:
                break
            
            progress = self.get_recording_progress()
            print(f"Tiempo transcurrido: {elapsed:.1f}s | Restante: {remaining:.1f}s | Progreso: {progress:.1f}%")
            time.sleep(update_interval)
        
        print("Grabación completada :) .\n")
    
    def view_stream(self, duration=None):
        """
        Visualiza el stream de EEG en tiempo real.
        
        Args:
            duration: Tiempo en segundos para visualizar (None = indefinido hasta cerrar ventana)
        """
        mi_muse = self.confirm_pairing()
        if mi_muse:
            print("******** Viewing Stream ********")
            if duration:
                print(f"Visualizando stream por {duration} segundos...")
                
                # Iniciar timer
                self.recording_start_time = time.time()
                self.is_recording = True
                
                # Ejecutar view() en un thread separado porque es blocking
                # Estamos dándole un thread nuevo para que se ejecute en paralelo.
                view_thread = threading.Thread(target=muse.view, daemon=True)
                view_thread.start()
                
                # Monitorear el tiempo mientras view() corre
                while self.is_recording:
                    is_active, elapsed, remaining = self.recording_timer()
                    if elapsed >= duration:
                        self.is_recording = False
                        print(f"\n Visualización completada por ({duration}s).")
                        print("CERRARla ventana MANUALMENTE para terminar.")
                        break
                    time.sleep(0.1)
                
            else:
                print("Visualizando stream (cierra la ventana para terminar)...")
                muse.view()
            
        else:
            print("No se pudo iniciar la visualización ❌ Muse no está emparejada.")


        

        

    




    
  