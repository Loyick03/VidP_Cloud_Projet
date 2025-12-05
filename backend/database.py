import json
from pathlib import Path
from typing import Dict

from .models import VideoMetadata

# Dossier où se trouve ce fichier (backend/)
BASE_DIR = Path(__file__).resolve().parent

# Fichier JSON qui sert de "base de données"
DB_FILE = BASE_DIR / "data.json"


def load_db() -> Dict[str, VideoMetadata]:
    """
    Charge la base de données depuis data.json si le fichier existe.
    Retourne un dict {video_id: VideoMetadata}
    """
    if DB_FILE.exists():
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # on reconstruit des objets VideoMetadata
            return {k: VideoMetadata(**v) for k, v in data.items()}
    return {}  # aucune vidéo encore enregistrée


def save_db(db: Dict[str, VideoMetadata]) -> None:
    """
    Sauvegarde la base de données dans data.json au format JSON.
    """
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v.dict() for k, v in db.items()}, f, indent=4)


#  Très important : on crée ici la base en mémoire
DB: Dict[str, VideoMetadata] = load_db()