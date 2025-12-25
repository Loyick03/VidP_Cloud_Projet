import time
import os
import json
import whisper
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
INPUT_FOLDER = "/mnt/data/input"       # Mappé sur 01_working
OUTPUT_FOLDER = "/mnt/data/processed"  # Mappé sur 02_metadata
# Chemin vers le modèle LOCAL (mappé depuis Windows)
MODEL_PATH = "/root/.cache/whisper/tiny.pt"

class LangHandler(FileSystemEventHandler):
    def __init__(self):
        print(f"⏳ Chargement Whisper (tiny)...", flush=True)
        
        # CHARGEMENT ROBUSTE DU MODÈLE LOCAL
        if os.path.exists(MODEL_PATH):
            print(f"📂 Chargement depuis cache local : {MODEL_PATH}", flush=True)
            self.model = whisper.load_model(MODEL_PATH)
        else:
            print(f"⚠️ Cache introuvable ({MODEL_PATH}) ! Tentative de téléchargement secours...", flush=True)
            self.model = whisper.load_model("tiny")
            
        print("✅ Lang-Ident Ready.", flush=True)

    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        
        # Filtre sur l'extension et les fichiers temporaires
        if not filename.endswith("_downscaled.mp4"): return
        if filename.startswith("TEMP_"): return

        print(f"\n[LANG] 🌍 Détecté : {filename}", flush=True)
        time.sleep(1)
        self.detect_language(event.src_path, filename)

    # --- C'EST ICI QU'ELLE DOIT ÊTRE (Indentation dans la classe) ---
    def detect_language(self, file_path, filename):
        try:
            print(f"--> Analyse langue pour {filename}...", flush=True)
            
            # Transcription (seulement les 30 premières secondes par défaut)
            audio = whisper.load_audio(file_path)
            audio = whisper.pad_or_trim(audio)
            
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            print(f"[RESULT] Langue : {detected_lang.upper()}", flush=True)

            # Création du JSON
            base_name = filename.replace("_downscaled.mp4", "")
            json_filename = f"{base_name}_lang.json"
            json_path = os.path.join(OUTPUT_FOLDER, json_filename)

            data = {
                "file": filename, 
                "language": detected_lang,
                "confidence": probs[detected_lang]
            }
            
            with open(json_path, 'w') as f:
                json.dump(data, f)
            
            print(f"[SUCCESS] JSON écrit : {json_filename}", flush=True)

        except Exception as e:
            print(f"[ERROR] {e}", flush=True)

# --- FIN DE LA CLASSE ---

def scan_existing_files(handler):
    print("🔍 Scan des fichiers en attente (Rattrapage)...", flush=True)
    if not os.path.exists(INPUT_FOLDER): return
    
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_downscaled.mp4")]
    
    if not files:
        print("   Aucun fichier en attente.", flush=True)

    for filename in files:
        # On vérifie si le travail est déjà fait
        json_check = os.path.join(OUTPUT_FOLDER, filename.replace("_downscaled.mp4", "_lang.json"))
        if not os.path.exists(json_check):
            print(f"   Rattrapage : {filename}", flush=True)
            # Maintenant ça marchera car la méthode existe dans handler
            handler.detect_language(os.path.join(INPUT_FOLDER, filename), filename)
        else:
            print(f"   Déjà traité : {filename}", flush=True)

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER, exist_ok=True)
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    handler = LangHandler()
    
    # 1. Rattrapage au démarrage
    scan_existing_files(handler)
    
    # 2. Surveillance temps réel
    observer = Observer()
    observer.schedule(handler, path=INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()