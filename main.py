#!/usr/bin/env python3
"""
Sistema de Grabación EEG - Muse 2
===================================
Punto de entrada único para todas las grabaciones.

PREREQUISITO: Debe estar corriendo 'muselsl stream' en otra terminal
"""

from scripts.variable_handling import CualitativeSurvey
from scripts.eeg_recording import EEGRecorder
from scripts.data_compiler_ui import AudioCues
import sys
import time
from pathlib import Path


def sesion_hibrida_simple():
    """Sesión híbrida simple con un trial MI/REST con audio cues"""
    from pylsl import StreamInlet, resolve_byprop
    import pandas as pd
    
    print("\n" + "="*60)
    print("  SESIÓN HÍBRIDA (MI + REST con Audio Cues)")
    print("="*60 + "\n")
    
    # Survey
    print("--- Encuesta Cualitativa ---")
    survey_filename = input("Nombre del archivo (sin extensión): ").strip()
    if not survey_filename:
        survey_filename = "hybrid_test"
    
    participant_id = input("ID del participante (default 001): ").strip()
    if not participant_id:
        participant_id = "001"
    
    my_survey = CualitativeSurvey(filename=survey_filename, p_id=participant_id)
    my_survey.init_csv()
    responses = my_survey.ask_initial_survey()
    my_survey.save_survey_response(initial_response=responses)
    
    print("\n✓ Encuesta completada.\n")
    
    # Configuración híbrida
    print("--- Configuración Híbrida ---")
    print("\nEjemplos de movimientos:")
    print("  - cerrar el puño derecho")
    print("  - cerrar el puño izquierdo")
    print("  - levantar la mano derecha")
    movement = input("\nDescribe el movimiento a imaginar: ").strip()
    if not movement:
        movement = "cerrar el puño derecho"
    
    mi_dur = input("Duración Motor Imagery en segundos (default 5): ").strip()
    mi_dur = int(mi_dur) if mi_dur.isdigit() else 5
    
    rest_dur = input("Duración REST en segundos (default 10): ").strip()
    rest_dur = int(rest_dur) if rest_dur.isdigit() else 10
    
    ciclos = input("Número de ciclos (default 2): ").strip()
    ciclos = int(ciclos) if ciclos.isdigit() else 2
    
    # Preparar grabación
    output_path = f"new_data/cuantitative/_{participant_id}_{survey_filename}_{time.strftime('%Y%m%d')}.csv"
    Path("new_data/cuantitative").mkdir(parents=True, exist_ok=True)
    
    print(f"\n*** Grabación Híbrida: Motor Imagery ***")
    print(f"Movimiento: {movement}")
    print(f"Configuración: {ciclos} ciclos × ({mi_dur}s MI + {rest_dur}s REST)")
    print(f"Duración total: {ciclos * (mi_dur + rest_dur)}s\n")
    print("Buscando stream LSL...")
    
    try:
        streams = resolve_byprop('type', 'EEG', timeout=5)
        
        if not streams:
            print("❌ No se encontró el stream EEG.")
            return
        
        inlet = StreamInlet(streams[0], max_chunklen=12)
        info = inlet.info()
        
        # Obtener canales
        ch = info.desc().child('channels').first_child()
        ch_names = []
        for _ in range(info.channel_count()):
            ch_names.append(ch.child_value('label'))
            ch = ch.next_sibling()
        
        print(f"✓ Conectado: {info.name()}")
        print(f"  Canales: {ch_names}\n")
        
        # Countdown
        print("Preparándose...")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        all_samples = []
        timestamps = []
        labels = []
        
        print()
        AudioCues.session_start()
        print()
        
        for cycle in range(ciclos):
            # MOTOR IMAGERY
            AudioCues.phase_transition("MOTOR IMAGERY")
            print(f"[Ciclo {cycle+1}/{ciclos}] >>> IMAGINA: {movement} - {mi_dur}s <<<\n")
            
            mi_start = time.time()
            while time.time() - mi_start < mi_dur:
                sample, timestamp = inlet.pull_sample(timeout=0.1)
                if sample:
                    all_samples.append(sample)
                    timestamps.append(timestamp)
                    labels.append('MI')
            
            # REST
            AudioCues.phase_transition("DESCANSO")
            print(f"[Ciclo {cycle+1}/{ciclos}] >>> DESCANSA - {rest_dur}s <<<\n")
            
            rest_start = time.time()
            while time.time() - rest_start < rest_dur:
                sample, timestamp = inlet.pull_sample(timeout=0.1)
                if sample:
                    all_samples.append(sample)
                    timestamps.append(timestamp)
                    labels.append('REST')
        
        # Guardar
        df = pd.DataFrame(all_samples, columns=ch_names)
        df['timestamps'] = timestamps
        df['label'] = labels
        df.to_csv(output_path, index=False)
        
        print()
        AudioCues.recording_complete()
        print(f"\n✓ Guardado en: {output_path}")
        print(f"  Muestras: {len(all_samples)} (MI: {labels.count('MI')} | REST: {labels.count('REST')})\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def sesion_completa():
    """Sesión completa con múltiples estados y audio cues"""
    print("\n" + "="*60)
    print("  SESIÓN COMPLETA DE INVESTIGACIÓN")
    print("="*60 + "\n")
    
    # Importar el sistema completo
    try:
        from scripts.data_compiler_ui import (
            verify_stream, 
            configure_session, 
            MotorIntentDataAcquisition
        )
        
        # Verificar stream
        if not verify_stream():
            print("\n Stream no detectado.")
            return
        
        # Configurar sesión
        config = configure_session()
        
        # Crear y ejecutar sesión
        acquisition = MotorIntentDataAcquisition(config)
        
        try:
            acquisition.run_session()
        except KeyboardInterrupt:
            print("\n\n  Sesión interrumpida por el usuario.")
            print(f"Trials completados: {len(acquisition.session_metadata)}")
            if acquisition.session_metadata:
                acquisition.save_session_metadata()
        except Exception as e:
            print(f"\n Error durante la sesión: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"\n Error al importar módulos de sesión completa: {e}")
        print("Verifica que data_compiler_ui.py esté disponible.")


def main():
    """Menú principal"""
    print("\n" + "="*70)
    print("  SISTEMA DE GRABACIÓN EEG - MUSE 2")
    print("="*70)
    
    print("\nSelecciona el tipo de grabación:\n")
    print("  1. Sesión Híbrida Simple")
    print("     • Un trial híbrido con audio cues")
    print("     • Alternando MI + REST con etiquetas")
    print("     • Configurable y rápido\n")
    
    print("  2. Sesión Completa de Investigación")
    print("     • Múltiples estados y trials")
    print("     • Audio cues profesionales")
    print("     • Metadata detallada")
    print("     • Encuestas pre/post\n")
    
    opcion = input("Elige una opción (1 o 2): ").strip()
    
    if opcion == "2":
        sesion_completa()
    else:
        sesion_hibrida_simple()


if __name__ == "__main__":
    main()
