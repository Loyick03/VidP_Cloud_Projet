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

## Installation & Démarrage

### Prérequis
- Docker & Docker Compose
- Python 3.9+

### Comment lancer le projet
1. **Cloner le repo** :
   ```bash
   git clone [https://github.com/Loyick03/VidP_Cloud_Projet.git](https://github.com/Loyick03/VidP_Cloud_Projet.git)
   cd VidP_Cloud_Projet
   
Guide de Test - Projet VidP
Ce document décrit la procédure étape par étape pour valider le fonctionnement de la pipeline DevOps VidP, de l'ingestion de la vidéo jusqu'à son affichage sur le Cloud.

Prérequis
Avant de commencer, assurez-vous d'avoir :
Docker & Docker Compose installés et lancés.
Une vidéo de test au format .mp4 (ex: test_video.mp4).
Accès Internet (pour l'envoi vers le Cloud AWS).

Phase 1 : Installation & Démarrage
1. Clonage et Préparation
Récupérez le projet et placez-vous à la racine :

Bash

git clone https://github.com/VOTRE_REPO/vidp-project.git
cd vidp-project
