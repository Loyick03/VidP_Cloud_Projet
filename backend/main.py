import shutil
import os
import json
import time
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permettre à tout le monde d'accéder (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Création du dossier static pour stocker les vidéos reçues
os.makedirs("static", exist_ok=True)

# On rend le dossier "static" accessible publiquement (pour lire les vidéos)
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_FILE = "simulated_dynamodb.json"

# --- ROUTE 1 : Afficher le site Web ---
@app.get("/")
async def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "Veuillez créer le fichier index.html"}

# --- ROUTE 2 : Recevoir les Métadonnées (JSON) ---
@app.post("/upload_result")
async def upload_result(request: Request):
    new_data = await request.json()
    # On utilise le nom de la vidéo comme ID unique
    video_id = new_data.get("video_id", f"vid_{int(time.time())}")
    
    print(f"JSON reçu pour : {video_id}")

    # 1. Charger l'historique existant
    db_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                db_data = json.load(f)
        except:
            db_data = {}

    # 2. Ajouter/Mettre à jour la vidéo
    db_data[video_id] = new_data

    # 3. Sauvegarder sur le disque
    with open(DB_FILE, "w") as f:
        json.dump(db_data, f, indent=4)

    return {"status": "success", "id": video_id}

# --- ROUTE 3 : Recevoir la Vidéo (MP4) ---
# C'est ICI que ton script local va envoyer le fichier
@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    file_location = f"static/{file.filename}"
    print(f"VIDÉO reçue : {file.filename}")
    
    # Écriture du fichier sur le disque du serveur
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"info": "Vidéo sauvegardée", "filename": file.filename}

# --- ROUTE 4 : API pour le Frontend (Donner la liste des vidéos) ---
@app.get("/api/results")
async def get_results():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}