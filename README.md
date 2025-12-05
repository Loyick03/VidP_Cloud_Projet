VidP_Cloud_Projet – Backend VidP Cloud (Service Métadonnées)

Ce dossier contient le backend officiel du projet VidP Cloud.
Il expose une API REST (FastAPI) qui reçoit, stocke et fournit les métadonnées des vidéos produites par le conteneur IA, et les met à disposition du frontend.


 Rôle dans l’architecture globale

 Conteneur IA (rôle 2)
	•	Downscale les vidéos
	•	Détecte la langue
	•	Génère les sous-titres
	•	Détecte les animaux
 Envoie les métadonnées vers le backend (POST /metadata)

Backend (rôle 3 – ce service)
	•	Reçoit les métadonnées via FastAPI
	•	Les stocke dans un fichier JSON persistant (backend/data.json)
	•	Permet au frontend de récupérer ces infos via des endpoints REST (GET /videos/{id})

📁 Structure du dossier backend/

backend/
├── __init__.py      # Indique que 'backend' est un package Python
├── main.py          # Définition de l'API FastAPI et des endpoints
├── models.py        # Définition du modèle VideoMetadata (Pydantic)
├── database.py      # Gestion du stockage : load_db(), save_db(), DB
├── utils.py         # Fonctions utilitaires (future extension)
└── data.json        # Stockage persistant des vidéos (généré automatiquement)

 1- Installation & Lancement (pour quelqu’un qui clone depuis GitHub)

git clone https://github.com/<username>/VidP_Cloud_Projet.git
cd VidP_Cloud_Projet

2- Créer et activer un environnement virtuel (Windows)

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

 Explication :
Windows bloque les scripts .ps1.
L’activation du venv nécessite d’autoriser temporairement leur exécution.
Le paramètre -Scope Process garantit que ça n’impacte pas le système après fermeture.

3- Installer les dépendances

pip install --upgrade pip
pip install fastapi uvicorn[standard] pydantic

4- IMPORTANT : lancer uvicorn depuis la racine du projet, pas depuis backend/

--Ne pas faire:
cd backend
uvicorn main:app ...

--Correct (depuis VidP_Cloud_Projet) :
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Pourquoi ?
	•	Python a besoin de savoir que backend est un package,
	•	et qu’il contient main.py, models.py, etc.
	•	Si on lance depuis l’intérieur du dossier backend/, les imports relatifs échouent (attempted relative import with no known parent package).


API – Documentation (Swagger)

Une fois uvicorn lancé :
	•	API : http://127.0.0.1:8000
	•	Docs interactives Swagger : http://127.0.0.1:8000/docs

Modèle des Métadonnées (VideoMetadata):

class VideoMetadata(BaseModel):
    video_id: str
    video_path: str
    subtitle_path: str
    language: str
    animals: List[str] = []
    duration_seconds: Optional[float] = None
)


Endpoints de l’API

✔️ 1. GET /

Vérifie que le backend tourne.

✔️ 2. POST /metadata

Recevoir les métadonnées d’une vidéo (appelé par l’IA).

✔️ 3. GET /videos/{video_id}

Récupérer les infos d’une vidéo (appelé par le frontend).

✔️ 4. Optionnel : GET /videos

Lister toutes les vidéos stockées.

⸻

 Persistance des données

Les données envoyées par l’IA sont automatiquement :
	•	stockées dans la variable DB (mémoire)
	•	sauvegardées dans backend/data.json grâce à save_db()

Tests rapides:
Le fichier  backend/data.json grâce à save_db() vous entrera les résultats de données fictives collecté lors du test apres avoir monté le système.



Points importants (tirés de notre expérience réelle)

Ces points éviteront aux autres membres les mêmes galères :
	•	Sous Windows, il faut autoriser temporairement l’exécution des scripts pour activer .venv
	•	Le backend doit être lancé depuis la racine, sinon les imports relatifs échouent
(attempted relative import with no known parent package)
	•	data.json n’est généré qu’après le premier POST /metadata
	•	backend/__init__.py doit exister pour que Python reconnaisse le package
	•	L’architecture doit rester propre pour que le déploiement dans la VM soit simple