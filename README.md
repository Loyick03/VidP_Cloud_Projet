# VidP - Pipeline de Traitement Vidéo Automatisé avec IA

## Description
VidP est une solution DevOps complète qui automatise le traitement de vidéos. Une vidéo déposée localement traverse une chaîne de conteneurs Docker (Redimensionnement, Identification de langue, Sous-titrage, Détection d'animaux via YOLO) et est automatiquement envoyée vers un serveur Cloud (AWS) pour être visionnée sur une interface Web type Netflix.

## Architecture
Le projet se divise en deux parties :
1. **L'Usine (Local - Docker Compose)** :
   - `downscaler` : Réduit la résolution (FFmpeg).
   - `lang-ident` : Détecte la langue audio (Faster-Whisper).
   - `subtitler` : Génère les sous-titres (Faster-Whisper).
   - `animal-detect` : Détecte les animaux (YOLOv8) et envoie le tout au Cloud.
   - **Monitoring** : Stack complète Prometheus + Grafana.

2. **Le Showroom (Cloud - AWS)** :
   - API Backend (FastAPI).
   - Frontend HTML/JS dynamique.

## Guide de Test - Projet VidP
Ce document décrit la procédure étape par étape pour valider le fonctionnement de la pipeline DevOps VidP, de l'ingestion de la vidéo jusqu'à son affichage sur le Cloud.

### Prérequis
Avant de commencer, assurez-vous d'avoir :
Docker & Docker Compose installés et lancés.
Une vidéo de test au format .mp4 (ex: test_video.mp4).
Accès Internet (pour l'envoi vers le Cloud AWS).

### Phase 1 : Installation & Démarrage
1. Clonage et Préparation
Récupérez le projet et placez-vous à la racine :

`bash
git clone https://github.com/VOTRE_REPO/vidp-project.git
cd vidp-project`

2. Création de l'environnement de données
Le projet utilise des volumes locaux pour simuler le passage de données entre conteneurs. Assurez-vous que l'arborescence est propre :

Bash

# Nettoyage d'anciens tests (optionnel)
`rm -rf data/00_input/* data/01_working/* data/02_metadata/* data/03_output/*`
# Création des dossiers (si non présents via git)
`mkdir -p data/00_input data/01_working data/02_metadata data/03_output`
3. Lancement de l'Infrastructure Locale
Lancez la stack de conteneurs (Traitement + Monitoring) :

`Bash
docker-compose up --build`

### Phase 2 : Exécution du Scénario de Test
Scénario : "Traitement complet d'une vidéo animalière"
Objectif : Vérifier que la vidéo traverse les 4 conteneurs et arrive sur le site Web.

Étape 1 : Injection (Trigger)
Ouvrez un autre terminal ou votre explorateur de fichiers. Copiez votre vidéo de test dans le dossier d'entrée :

`Bash
cp chemin/vers/ma_video.mp4 ./data/00_input/`

Étape 2 : Validation des Logs (Monitoring Actif)
Observez le terminal où tourne Docker Compose. Vous devez voir la séquence suivante :

[dowscale] : Détecte le fichier et lance FFmpeg.

Succès : Fichier _downscaled.mp4 créé dans data/01_working.

[detectlang] & [subtitles] : Se déclenchent simultanément sur la vidéo redimensionnée.

Succès : Fichiers _lang.json et _subs.srt créés dans data/02_metadata.

[animal-detect] : Détecte la vidéo, attend les métadonnées, puis lance YOLO.

Log attendu : [ANIMAL] Détecté : ... suivi de SUCCÈS LOCAL !.

Log final : VIDÉO UPLOADÉE AVEC SUCCÈS SUR LE CLOUD !.

Étape 3 : Validation Visuelle (Monitoring Grafana)
Pendant le traitement, ouvrez votre navigateur :

`URL : http://localhost:3000`

Action : Observez les pics de consommation CPU/RAM correspondant à l'activation des conteneurs d'IA.

Phase 3 : Validation du Résultat (Cloud)
Une fois le log VIDÉO UPLOADÉE apparu dans le terminal :

Ouvrez le frontend Cloud (AWS) : http://51.20.183.135:8000 (ou votre IP actuelle).
