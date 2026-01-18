import time
import os
import json
import requests  # Nécessaire pour parler à AWS
from ultralytics import YOLO
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
INPUT_FOLDER = "/mnt/data/processed"
META_FOLDER = "/mnt/data/metadata"
FINAL_FOLDER = "/mnt/data/final"
LOCAL_MODEL = "/root/.cache/yolo/yolov8n.pt"

# On récupère l'URL AWS depuis le docker-compose
# Exemple attendu : http://51.20.183.135:8000/upload_result
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/upload_result")

class AnimalHandler(FileSystemEventHandler):
    def __init__(self):
        print("⏳ Chargement YOLO...", flush=True)
        if os.path.exists(LOCAL_MODEL):
            self.model = YOLO(LOCAL_MODEL)
            print("✅ Modèle chargé depuis le cache.", flush=True)
        else:
            print("⚠️ Cache absent, utilisation défaut.", flush=True)
            self.model = YOLO("yolov8n.pt")

    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        if not filename.endswith("_downscaled.mp4"): return

        print(f"\n[ANIMAL] 🐶 Détecté : {filename}", flush=True)
        time.sleep(2)
        self.process_pipeline(event.src_path, filename)

    def process_pipeline(self, file_path, filename):
        print(f"DEBUG: Entrée fonction process pour {filename}", flush=True)
        base_name = filename.replace("_downscaled.mp4", "")
        
        # 1. Analyse YOLO (Mode Streaming optimisé)
        print(f"--> 🧠 Lancement YOLO (Mode Stream) sur {filename}...", flush=True)
        
        animals_found = set()
        frame_count = 0
        
        try:
            results_generator = self.model.predict(file_path, save=False, stream=True, conf=0.4, verbose=False)
            print("    Progression : ", end="", flush=True)
            
            for r in results_generator:
                frame_count += 1
                if frame_count % 20 == 0:
                    print(".", end="", flush=True)
                
                for c in r.boxes.cls:
                    class_name = self.model.names[int(c)]
                    if class_name not in animals_found:
                        animals_found.add(class_name)
                        print(f"[{class_name}]", end="", flush=True)

            print(f"\n✅ Terminé ! {frame_count} frames analysées.")
            animals_list = list(animals_found)
            print(f"✅ [RESULT] Total animaux : {animals_list}", flush=True)
            
        except Exception as e:
            print(f"\n❌ CRASH YOLO : {e}", flush=True)
            return

        # 2. Attente des fichiers metadata (Générés par les autres conteneurs)
        lang_file = os.path.join(META_FOLDER, f"{base_name}_lang.json")
        subs_file = os.path.join(META_FOLDER, f"{base_name}_subs.srt")
        
        print(f"--> ⏳ Vérification metadata...", flush=True)
        
        # On attend jusqu'à 2 minutes que les sous-titres et la langue soient prêts
        for i in range(60): 
            if os.path.exists(lang_file) and os.path.exists(subs_file):
                self.finalize(filename, animals_list, lang_file, subs_file)
                return
            time.sleep(2)
            if i % 5 == 0: print("w", end="", flush=True)

        print("\n[TIMEOUT] ❌ Manque Langue ou Sous-titres après 2 minutes.", flush=True)

    def finalize(self, filename, animals, lang_file, subs_file):
        try:
            # A. Lecture du fichier langue
            with open(lang_file, 'r') as f:
                lang_data = json.load(f)

            # B. Lecture complète des sous-titres
            try:
                with open(subs_file, 'r', encoding='utf-8') as f:
                    subs_content = f.read()
            except:
                subs_content = "Erreur lecture sous-titres"

            # C. Sauvegarde Locale (Backup)
            payload_local = {
                "video_name": filename,
                "animals_detected": animals,
                "audio_language": lang_data.get("language", "unknown"),
                "subtitles_path": subs_file,
                "processed_at": time.ctime()
            }
            
            base_name = filename.replace("_downscaled.mp4", "")
            final_filename = f"{base_name}_final_result.json"
            final_path = os.path.join(FINAL_FOLDER, final_filename)

            with open(final_path, 'w', encoding='utf-8') as f:
                json.dump(payload_local, f, indent=4, ensure_ascii=False)

            print("\n------------------------------------------------", flush=True)
            print(f" ✅ SUCCÈS LOCAL ! Résultat dans : {final_filename}", flush=True)

            # --- D. ENVOI VERS AWS (MÉTADONNÉES) ---
            print(f" 📡 Envoi des DONNÉES vers : {BACKEND_URL} ...", flush=True)
            
            # Payload pour le Cloud
            aws_payload = {
                "video_id": base_name,
                "filename": filename,
                "original_resolution": "1080p", 
                "processed_resolution": "720p",
                "detected_language": lang_data.get("language", "unknown"),
                "subtitles": subs_content, # Contenu complet des SRT
                "detected_objects": animals,
                "s3_url": f"/static/{filename}", # URL relative pour le frontend
                "timestamp": time.time()
            }

            try:
                # 1. Envoi du JSON
                response = requests.post(BACKEND_URL, json=aws_payload, timeout=50)
                if response.status_code in [200, 201]:
                    print(f" ✅ AWS JSON REÇU : {response.json()}")
                else:
                    print(f" ⚠️ AWS JSON ERREUR : {response.status_code} - {response.text}")
                
                # 2. Envoi de la VIDÉO (Upload physique)
                video_full_path = os.path.join(INPUT_FOLDER, filename)
                
                # On déduit l'URL vidéo : http://.../upload_result -> http://.../upload_video
                video_url = BACKEND_URL.replace("/upload_result", "/upload_video")
                
                print(f" 📡 Envoi du FICHIER VIDÉO vers : {video_url} ...")
                
                if os.path.exists(video_full_path):
                    with open(video_full_path, 'rb') as f_vid:
                        # 'file' est le nom du champ attendu par FastAPI
                        files = {'file': (filename, f_vid, 'video/mp4')}
                        resp_vid = requests.post(video_url, files=files, timeout=1000) # Timeout long pour la vidéo
                        
                        if resp_vid.status_code == 200:
                            print(" 🚀 VIDÉO UPLOADÉE AVEC SUCCÈS SUR LE CLOUD !")
                        else:
                            print(f" ❌ ERREUR UPLOAD VIDÉO : {resp_vid.status_code} - {resp_vid.text}")
                else:
                    print(" ⚠️ Fichier vidéo introuvable sur le disque local.")

            except Exception as e:
                print(f" ❌ ERREUR CONNEXION AWS : {e}")
                print("    (Vérifie que le serveur AWS est lancé et le port 8000 ouvert)")

            print("------------------------------------------------", flush=True)
            
        except Exception as e:
            print(f"[ERROR] Finalisation : {e}", flush=True)

def scan_existing_files(handler):
    print("🔍 Scan des fichiers...", flush=True)
    if not os.path.exists(INPUT_FOLDER): return
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_downscaled.mp4")]
    for filename in files:
        final_check = os.path.join(FINAL_FOLDER, filename.replace("_downscaled.mp4", "_final_result.json"))
        # On force le retraitement si le fichier final n'existe pas
        if not os.path.exists(final_check):
            print(f"   Rattrapage : {filename}", flush=True)
            handler.process_pipeline(os.path.join(INPUT_FOLDER, filename), filename)
        else:
             print(f"   Déjà terminé : {filename}", flush=True)

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER, exist_ok=True)
    if not os.path.exists(META_FOLDER): os.makedirs(META_FOLDER, exist_ok=True)
    if not os.path.exists(FINAL_FOLDER): os.makedirs(FINAL_FOLDER, exist_ok=True)

    handler = AnimalHandler()
    scan_existing_files(handler)

    observer = Observer()
    observer.schedule(handler, path=INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()