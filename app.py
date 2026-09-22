"""
ViyaSave - Téléchargeur de vidéos TikTok sans filigrane
Backend Flask + yt-dlp
"""
import os
import re
import shutil
import tempfile
import time
from collections import defaultdict, deque

from flask import Flask, jsonify, render_template, request, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

# Seuls les liens TikTok sont acceptés
TIKTOK_REGEX = re.compile(
    r"^https?://(www\.|m\.|vm\.|vt\.)?tiktok\.com/[^\s]+$", re.IGNORECASE
)

# Format : la meilleure version SANS filigrane (yt-dlp marque les autres "watermarked")
FORMAT_SANS_FILIGRANE = "best[format_note!*=watermark]/best"

# --- Limitation simple : 10 requêtes par minute et par adresse IP ---
LIMITE = 10
FENETRE = 60
_requetes = defaultdict(deque)


def trop_de_requetes(ip: str) -> bool:
    maintenant = time.time()
    file = _requetes[ip]
    while file and maintenant - file[0] > FENETRE:
        file.popleft()
    if len(file) >= LIMITE:
        return True
    file.append(maintenant)
    return False


def ip_client() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()


def lien_valide(url: str) -> bool:
    return bool(url) and bool(TIKTOK_REGEX.match(url.strip()))


def options_base() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": FORMAT_SANS_FILIGRANE,
    }


@app.route("/")
def accueil():
    return render_template("index.html")


@app.route("/conditions")
def conditions():
    return render_template("conditions.html")


@app.post("/api/info")
def infos_video():
    """Renvoie le titre, l'auteur et la miniature avant le téléchargement."""
    if trop_de_requetes(ip_client()):
        return jsonify(erreur="Trop de demandes. Réessayez dans une minute."), 429

    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not lien_valide(url):
        return jsonify(erreur="Lien invalide. Collez un lien TikTok (ex : https://www.tiktok.com/@nom/video/123...)."), 400

    try:
        with yt_dlp.YoutubeDL(options_base()) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return jsonify(erreur="Impossible de récupérer cette vidéo. Elle est peut-être privée ou supprimée."), 422

    return jsonify(
        titre=info.get("title") or info.get("description") or "Vidéo TikTok",
        auteur=info.get("uploader") or info.get("creator") or "",
        miniature=info.get("thumbnail"),
        duree=info.get("duration"),
    )


@app.get("/api/download")
def telecharger():
    """Télécharge la vidéo sur le serveur puis l'envoie à l'utilisateur."""
    if trop_de_requetes(ip_client()):
        return "Trop de demandes. Réessayez dans une minute.", 429

    url = request.args.get("url", "").strip()
    if not lien_valide(url):
        return "Lien invalide.", 400

    dossier = tempfile.mkdtemp(prefix="viyasave_")

    @after_this_request
    def nettoyage(reponse):
        shutil.rmtree(dossier, ignore_errors=True)
        return reponse

    opts = options_base()
    opts["outtmpl"] = os.path.join(dossier, "%(id)s.%(ext)s")
    opts["max_filesize"] = 200 * 1024 * 1024  # 200 Mo max

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            chemin = ydl.prepare_filename(info)
    except Exception:
        return "Échec du téléchargement. Réessayez plus tard.", 422

    if not os.path.exists(chemin):
        return "Fichier introuvable.", 500

    nom = f"viyasave_{info.get('id', 'video')}.mp4"
    return send_file(chemin, as_attachment=True, download_name=nom, mimetype="video/mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
