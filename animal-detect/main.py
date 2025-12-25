import time
import os
import json
from ultralytics import YOLO
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
INPUT_FOLDER = "/mnt/data/processed"
META_FOLDER = "/mnt/data/metadata"
FINAL_FOLDER = "/mnt/data/final"
LOCAL_MODEL = "/root/.cache/yolo/yolov8n.pt"

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
            # stream=True est la clé pour économiser la RAM !
            # conf=0.4 : On abaisse un peu le seuil pour être sûr de capter les animaux
            results_generator = self.model.predict(file_path, save=False, stream=True, conf=0.4, verbose=False)
            
            print("    Progression : ", end="", flush=True)
            
            for r in results_generator:
                frame_count += 1
                # On affiche un point toutes les 20 frames pour montrer que ça bosse
                if frame_count % 20 == 0:
                    print(".", end="", flush=True)
                
                # Analyse des boîtes détectées sur cette frame
                for c in r.boxes.cls:
                    class_name = self.model.names[int(c)]
                    # On ajoute à la liste si c'est nouveau
                    if class_name not in animals_found:
                        animals_found.add(class_name)
                        # Petit bonus : on l'affiche tout de suite
                        print(f"[{class_name}]", end="", flush=True)

            print(f"\n✅ Terminé ! {frame_count} frames analysées.")
            animals_list = list(animals_found)
            print(f"✅ [RESULT] Total animaux : {animals_list}", flush=True)
            
        except Exception as e:
            print(f"\n❌ CRASH YOLO : {e}", flush=True)
            return

        # 2. Attente des fichiers metadata
        lang_file = os.path.join(META_FOLDER, f"{base_name}_lang.json")
        subs_file = os.path.join(META_FOLDER, f"{base_name}_subs.srt")
        
        print(f"--> ⏳ Vérification metadata...", flush=True)
        
        for i in range(60): 
            if os.path.exists(lang_file) and os.path.exists(subs_file):
                self.finalize(filename, animals_list, lang_file, subs_file)
                return
            time.sleep(2)
            if i % 5 == 0: print("w", end="", flush=True) # w for wait

        print("\n[TIMEOUT] ❌ Manque Langue ou Sous-titres après 2 minutes.", flush=True)

    def finalize(self, filename, animals, lang_file, subs_file):
        try:
            with open(lang_file, 'r') as f:
                lang_data = json.load(f)

            payload = {
                "video_name": filename,
                "animals_detected": animals,
                "audio_language": lang_data.get("language", "unknown"),
                "confidence": lang_data.get("confidence", 0.0),
                "subtitles_path": subs_file,
                "pipeline_status": "completed",
                "processed_at": time.ctime()
            }
            
            base_name = filename.replace("_downscaled.mp4", "")
            final_filename = f"{base_name}_final_result.json"
            final_path = os.path.join(FINAL_FOLDER, final_filename)

            with open(final_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)

            print("\n------------------------------------------------", flush=True)
            print(f" ✅ SUCCÈS TOTAL ! Résultat dans :", flush=True)
            print(f" 📂 {final_filename}", flush=True)
            print("------------------------------------------------", flush=True)
            
        except Exception as e:
            print(f"[ERROR] Ecriture finale : {e}", flush=True)

def scan_existing_files(handler):
    print("🔍 Scan des fichiers...", flush=True)
    if not os.path.exists(INPUT_FOLDER): return
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_downscaled.mp4")]
    for filename in files:
        final_check = os.path.join(FINAL_FOLDER, filename.replace("_downscaled.mp4", "_final_result.json"))
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