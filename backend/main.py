from fastapi import FastAPI
from .models import VideoMetadata
from .database import DB, save_db

app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend VM en ligne ✅"}


@app.post("/metadata")
def receive_metadata(meta: VideoMetadata):
    """
    Endpoint appelé par le conteneur IA pour envoyer les métadonnées.
    """
    DB[meta.video_id] = meta
    save_db(DB)
    return {"status": "saved", "video_id": meta.video_id}


@app.get("/videos/{video_id}")
def get_video(video_id: str):
    """
    Endpoint appelé par le frontend pour récupérer les infos d'une vidéo.
    """
    if video_id not in DB:
        return {"error": "video not found"}
    return DB[video_id]