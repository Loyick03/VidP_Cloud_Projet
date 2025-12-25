import time
import os
import whisper
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

INPUT_FOLDER = "/mnt/data/input"
OUTPUT_FOLDER = "/mnt/data/metadata"

class SubtitleHandler(FileSystemEventHandler):
    def __init__(self):
        print("Chargement Whisper (base)...", flush=True)
        model_path = "/root/.cache/whisper/base.pt"
        print(f"Chargement depuis cache local : {model_path}", flush=True)
        self.model = whisper.load_model(model_path)
        print("Subtitler Ready.", flush=True)

    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)

        # 1. On vérifie que c'est bien un fichier vidéo du downscaler
        if not filename.endswith("_downscaled.mp4"): return
        filename = os.path.basename(event.src_path)
        # 2. On ignore les fichiers temporaires en cours d'écriture
        if filename.startswith("TEMP_"): return
        # ----------------------------

        print(f"\n[SUBS] 📝 Détecté : {filename}", flush=True)
        time.sleep(4)
        self.process_video(event.src_path, filename)

    def process_video(self, file_path, filename):
        print(f"--> 🎬 Démarrage transcription pour {filename}...", flush=True)
        try:
            # Transcription
            result = self.model.transcribe(file_path, fp16=False)
            
            base_name = filename.replace("_downscaled.mp4", "")
            srt_filename = f"{base_name}_subs.srt"
            srt_path = os.path.join(OUTPUT_FOLDER, srt_filename)
            
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(result["segments"]):
                    start = self.format_timestamp(segment["start"])
                    end = self.format_timestamp(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")
            
            print(f"[SUCCESS] 📝 SRT écrit : {srt_filename}", flush=True)

        except Exception as e:
            print(f"[ERROR] ❌ {e}", flush=True)

    def format_timestamp(self, seconds):
        millis = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        minutes %= 60
        seconds %= 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

# --- FONCTION DE RATTRAPAGE ---
def scan_existing_files(handler):
    print("🔍 Scan des fichiers existants au démarrage...", flush=True)
    # On regarde s'il y a déjà des fichiers dans le dossier
    if not os.path.exists(INPUT_FOLDER): return
    
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_downscaled.mp4")]
    
    if not files:
        print("   Aucun fichier en attente.", flush=True)
    
    for filename in files:
        print(f"   Rattrapage du fichier : {filename}", flush=True)
        file_path = os.path.join(INPUT_FOLDER, filename)
        # On traite le fichier directement
        handler.process_video(file_path, filename)

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER, exist_ok=True)
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 1. On initialise le Handler (et donc le modèle Whisper)
    handler = SubtitleHandler()

    # 2. On traite les fichiers qui sont DÉJÀ là (Rattrapage)
    scan_existing_files(handler)

    # 3. On lance la surveillance pour les PROCHAINS fichiers
    print("--- Démarrage de la surveillance ---", flush=True)
    observer = Observer()
    observer.schedule(handler, path=INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()