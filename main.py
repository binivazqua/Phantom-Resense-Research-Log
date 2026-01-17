

from scripts.data_compiler_ui import hybrid_session, static_session


def main():
    """Menú principal"""
    print("\n" + "="*70)
    print("  EEG - MUSE 2 RECORDING SYSTEM ")
    print("="*70)
    
    print("\nSelecciona el tipo de grabación:\n")
    print("  1. Sesión Híbrida")
    print("     • Alternando MI + REST con etiquetas")
    print("     • Audio cues profesionales")
    print("     • Configurable y flexible\n")
    
    print("  2. Sesión Completa de Investigación")
    print("     • Múltiples estados y trials")
    print("     • Audio cues profesionales")
    print("     • Metadata detallada")
    print("     • Encuestas pre/post\n")
    
    opcion = input("Elige una opción (1 o 2): ").strip()
    
    if opcion == "2":
        static_session()
    else:
        hybrid_session()


if __name__ == "__main__":
    main()
