from fastapi import FastAPI, HTTPException, status
from .models import VideoMetadata
from .database import DB, save_db

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend VM en ligne ✅"}

@app.post("/metadata", status_code=status.HTTP_201_CREATED)
def receive_metadata(meta: VideoMetadata):
    """
    Endpoint appelé par le conteneur IA pour envoyer les métadonnées.
    """
    # Optionnel : Vérifier si l'ID existe déjà pour éviter d'écraser
    if meta.video_id in DB:
        # Vous pouvez choisir d'écraser (update) ou de lever une erreur
        pass 

    DB[meta.video_id] = meta.dict() # .dict() ou .model_dump() selon version Pydantic
    
    try:
        save_db(DB)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde DB: {str(e)}")
        
    return {"status": "saved", "video_id": meta.video_id}

@app.get("/videos/{video_id}", response_model=VideoMetadata)
def get_video(video_id: str):
    """
    Endpoint appelé par le frontend pour récupérer les infos d'une vidéo.
    """
    if video_id not in DB:
        # on renvoie une vraie erreur 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    return DB[video_id]
