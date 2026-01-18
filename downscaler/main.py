import time
import os
import shutil  # Nécessaire pour déplacer les fichiers entre dossiers
import ffmpeg
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

INPUT_FOLDER = "/mnt/data/input"
OUTPUT_FOLDER = "/mnt/data/processed"
# Dossier de travail local (invisible pour les autres conteneurs)
LOCAL_STAGING_FOLDER = "/tmp/vidp_staging"

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        
        # Filtres basiques
        if filename.startswith("TEMP_") or filename.startswith("."): return
        if not filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')): return

        print(f"\n[DOWNSCALER] Nouvelle source : {filename}", flush=True)
        # Petit délai de sécurité pour la copie
        time.sleep(5)
        self.process_video(event.src_path, filename)

    def process_video(self, input_path, filename):
        try:
            base_name = os.path.splitext(filename)[0]
            final_filename = f"{base_name}_downscaled.mp4"
            
            # 1. Chemins
            # Le fichier est créé dans le dossier temporaire local (/tmp)
            staging_path = os.path.join(LOCAL_STAGING_FOLDER, final_filename)
            
            # Destination finale
            final_dest_path = os.path.join(OUTPUT_FOLDER, final_filename)
            # Destination intermédiaire (fichier caché dans le dossier final le temps du transfert)
            temp_dest_path = os.path.join(OUTPUT_FOLDER, f".tmp_{final_filename}")

            print(f"--> 1/3 Traitement FFmpeg en zone tampon ({LOCAL_STAGING_FOLDER})...", flush=True)
            
            # Nettoyage préventif si un vieux fichier traîne
            if os.path.exists(staging_path): os.remove(staging_path)

            # On lance FFmpeg vers le dossier STAGING (invisible pour les autres)
            (
                ffmpeg
                .input(input_path)
                .output(staging_path, vf='scale=-2:480', loglevel="error")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            print(f"--> 2/3 Transfert vers le dossier final...", flush=True)
            # On déplace d'abord sous un nom caché (.tmp_) pour éviter que les autres le voient pendant la copie
            shutil.move(staging_path, temp_dest_path)
            
            print(f"--> 3/3 Validation finale (Rename)...", flush=True)
            # Le renommage est atomique : le fichier apparaît d'un coup pour les autres services
            os.rename(temp_dest_path, final_dest_path)
            
            print(f"[SUCCESS] Vidéo prête et visible : {final_filename}", flush=True)

        except ffmpeg.Error as e:
            print(f"[ERROR] FFmpeg a échoué : {e.stderr.decode('utf8')}", flush=True)
            # Nettoyage en cas d'erreur
            if os.path.exists(staging_path): os.remove(staging_path)
        except Exception as e:
            print(f"[ERROR] Erreur inattendue : {e}", flush=True)

if __name__ == "__main__":
    # Création des dossiers nécessaires
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER, exist_ok=True)
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    if not os.path.exists(LOCAL_STAGING_FOLDER): os.makedirs(LOCAL_STAGING_FOLDER, exist_ok=True)
    
    print("--- DOWNSCALER (Mode Staging Sécurisé) READY ---", flush=True)
    
    # On vide le dossier staging au démarrage pour être propre
    for f in os.listdir(LOCAL_STAGING_FOLDER):
        os.remove(os.path.join(LOCAL_STAGING_FOLDER, f))

    observer = Observer()
    observer.schedule(VideoHandler(), path=INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()