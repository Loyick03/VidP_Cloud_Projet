import time
import os
import ffmpeg
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

INPUT_FOLDER = "/mnt/data/input"
OUTPUT_FOLDER = "/mnt/data/processed"

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        
        # On ignore les fichiers temporaires et les fichiers non vidéo
        if filename.startswith("TEMP_"): return
        if not filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')): return

        print(f"\n[DOWNSCALER] Nouvelle source : {filename}", flush=True)
        # Petit délai de sécurité au cas où la copie Windows
        time.sleep(6)
        self.process_video(event.src_path, filename)

    def process_video(self, input_path, filename):
        try:
            base_name = os.path.splitext(filename)[0]
            final_filename = f"{base_name}_downscaled.mp4"
            # NOM TEMPORAIRE (Invisible pour les autres)
            temp_filename = f"TEMP_{final_filename}"
            
            temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
            final_path = os.path.join(OUTPUT_FOLDER, final_filename)

            print(f"--> Traitement en cours (vers fichier temp)...", flush=True)
            
            # On lance FFmpeg vers le fichier TEMP
            (
                ffmpeg
                .input(input_path)
                .output(temp_path, vf='scale=-1:480', loglevel="error")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Une fois fini, on renomme.
            os.rename(temp_path, final_path)
            
            print(f"[SUCCESS] Vidéo prête : {final_filename}", flush=True)

        except ffmpeg.Error as e:
            print(f"[ERROR] FFmpeg a échoué : {e.stderr.decode('utf8')}", flush=True)
        except Exception as e:
            print(f"[ERROR] Erreur inattendue : {e}", flush=True)

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER, exist_ok=True)
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    print("--- DOWNSCALER (Mode Atomique) READY ---", flush=True)
    observer = Observer()
    observer.schedule(VideoHandler(), path=INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()