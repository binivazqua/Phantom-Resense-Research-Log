import muselsl as muse
from muselsl import record, list_muses
import time

class EEGRecorder:
    def __init__(self, duration, filename):
        self.duration = duration
        self.filename = filename
    
    # 1. CONFIRMAR PAIRING CON MUSE
    def confirm_pairing():
        paired = muse.list_muses()
        mi_muse = paired[0]
        if not paired:
            print(f"NO SE ENCONTRÓ LA MUSE 2.")
            return None
        else:
            print(f"SE ENCONTRÓ LA MUSE 2: {mi_muse['name']} - {mi_muse['address']}")
            return mi_muse

    




    
  