"""
ViyaSave - Téléchargeur de vidéos TikTok sans filigrane
Backend Flask + yt-dlp
"""
import os
import re
import shutil
import tempfile
import time
import hmac
import secrets
import traceback
from collections import defaultdict, deque
from datetime import timedelta

from flask import (Flask, abort, after_this_request, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from markupsafe import Markup
import markdown as md
import yt_dlp
from werkzeug.middleware.proxy_fix import ProxyFix

import db

app = Flask(__name__)
# Render est derrière un proxy : on récupère le vrai https et le vrai domaine
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
# SECRET_KEY : à définir dans Render (bouton « Generate ») pour garder la connexion admin
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=7)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")))

try:
    db.init()
except Exception:
    print("ERREUR base de données (init) :", flush=True)
    traceback.print_exc()


# --- Publicités et statistiques : tout se règle dans Render (Environment) ---
# GA_ID      : identifiant Google Analytics (ex : G-XXXXXXXXXX)
# AD_HEAD    : code publicitaire à placer dans <head> (optionnel)
# AD_TOP     : bannière affichée sous le titre
# AD_BOTTOM  : bannière affichée sous le résultat
# ADS_TXT    : contenu du fichier ads.txt demandé par la régie
@app.context_processor
def reglages_pub():
    return {
        "ga_id": os.environ.get("GA_ID", "").strip(),
        "ad_head": os.environ.get("AD_HEAD", ""),
        "ad_top": os.environ.get("AD_TOP", ""),
        "ad_bottom": os.environ.get("AD_BOTTOM", ""),
    }


@app.route("/ads.txt")
def ads_txt():
    contenu = os.environ.get("ADS_TXT", "").replace("\\n", "\n")
    if not contenu:
        return "", 404
    return contenu, 200, {"Content-Type": "text/plain; charset=utf-8"}

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
    try:
        articles = db.lister(publies_seulement=True, limite=3)
    except Exception:
        articles = []
    return render_template("index.html", derniers_articles=articles)


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
        print("ERREUR /api/info :", url, flush=True)
        traceback.print_exc()
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
        print("ERREUR /api/download :", url, flush=True)
        traceback.print_exc()
        return "Échec du téléchargement. Réessayez plus tard.", 422

    if not os.path.exists(chemin):
        return "Fichier introuvable.", 500

    nom = f"viyasave_{info.get('id', 'video')}.mp4"
    return send_file(chemin, as_attachment=True, download_name=nom, mimetype="video/mp4")


# =====================================================================
#  BLOG PUBLIC
# =====================================================================
@app.template_filter("markdown")
def filtre_markdown(texte):
    return Markup(md.markdown(texte or "", extensions=["extra", "sane_lists", "toc"]))


@app.template_filter("date_fr")
def filtre_date(iso):
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre"]
    try:
        a, m, j = iso[:10].split("-")
        return f"{int(j)} {mois[int(m) - 1]} {a}"
    except Exception:
        return ""


@app.route("/blog")
def blog():
    return render_template("blog_liste.html", articles=db.lister(publies_seulement=True))


@app.route("/blog/<slug>")
def article(slug):
    art = db.par_slug(slug)
    if not art or (not art["published"] and not session.get("admin")):
        abort(404)
    autres = [a for a in db.lister(publies_seulement=True, limite=4) if a["slug"] != slug][:3]
    return render_template("blog_article.html", art=art, autres=autres)


@app.route("/robots.txt")
def robots():
    base = request.url_root.rstrip("/")
    texte = f"User-agent: *\nDisallow: /admin\nDisallow: /api/\nSitemap: {base}/sitemap.xml\n"
    return texte, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/sitemap.xml")
def sitemap():
    base = request.url_root.rstrip("/")
    urls = [(f"{base}/", None), (f"{base}/blog", None)]
    for a in db.lister(publies_seulement=True):
        urls.append((f"{base}/blog/{a['slug']}", (a.get("updated_at") or "")[:10]))
    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        lignes.append(f"  <url><loc>{loc}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") + "</url>")
    lignes.append("</urlset>")
    return "\n".join(lignes), 200, {"Content-Type": "application/xml; charset=utf-8"}


# =====================================================================
#  PANEL ADMIN  (mot de passe : variable ADMIN_PASSWORD dans Render)
# =====================================================================
def admin_requis():
    if not session.get("admin"):
        return redirect(url_for("admin_connexion"))
    return None


def verifier_csrf():
    jeton = request.form.get("csrf", "")
    if not jeton or not hmac.compare_digest(jeton, session.get("csrf", "")):
        abort(400)


@app.context_processor
def jeton_csrf():
    return {"csrf": session.get("csrf", "")}


@app.route("/admin/connexion", methods=["GET", "POST"])
def admin_connexion():
    mot_de_passe = os.environ.get("ADMIN_PASSWORD", "")
    erreur = ""
    if not mot_de_passe:
        erreur = "Panel désactivé : ajoutez la variable ADMIN_PASSWORD dans Render."
    elif request.method == "POST":
        if trop_de_requetes(ip_client()):
            erreur = "Trop d'essais. Réessayez dans une minute."
        elif hmac.compare_digest(request.form.get("mot_de_passe", ""), mot_de_passe):
            session.clear()
            session.permanent = True
            session["admin"] = True
            session["csrf"] = secrets.token_hex(16)
            return redirect(url_for("admin_accueil"))
        else:
            erreur = "Mot de passe incorrect."
    return render_template("admin_connexion.html", erreur=erreur)


@app.route("/admin/deconnexion")
def admin_deconnexion():
    session.clear()
    return redirect(url_for("accueil"))


@app.route("/admin")
def admin_accueil():
    if (r := admin_requis()):
        return r
    return render_template("admin_liste.html", articles=db.lister(publies_seulement=False),
                           message=request.args.get("message", ""))


def _form_article():
    return dict(
        titre=request.form.get("titre", "").strip(),
        description=request.form.get("description", "").strip()[:300],
        contenu=request.form.get("contenu", ""),
        image=request.form.get("image", "").strip(),
        publie=request.form.get("publie") == "1",
        slug=request.form.get("slug", "").strip(),
    )


@app.route("/admin/nouveau", methods=["GET", "POST"])
def admin_nouveau():
    if (r := admin_requis()):
        return r
    if request.method == "POST":
        verifier_csrf()
        f = _form_article()
        if not f["titre"]:
            return render_template("admin_edition.html", art=None, f=f, erreur="Le titre est obligatoire.")
        db.creer(**f)
        return redirect(url_for("admin_accueil", message="Article enregistré ✅"))
    return render_template("admin_edition.html", art=None, f={}, erreur="")


@app.route("/admin/modifier/<int:article_id>", methods=["GET", "POST"])
def admin_modifier(article_id):
    if (r := admin_requis()):
        return r
    art = db.par_id(article_id) or abort(404)
    if request.method == "POST":
        verifier_csrf()
        f = _form_article()
        if not f["titre"]:
            return render_template("admin_edition.html", art=art, f=f, erreur="Le titre est obligatoire.")
        db.modifier(article_id, **f)
        return redirect(url_for("admin_accueil", message="Article mis à jour ✅"))
    f = dict(titre=art["title"], description=art["description"], contenu=art["content"],
             image=art["image"], publie=bool(art["published"]), slug=art["slug"])
    return render_template("admin_edition.html", art=art, f=f, erreur="")


@app.route("/admin/supprimer/<int:article_id>", methods=["POST"])
def admin_supprimer(article_id):
    if (r := admin_requis()):
        return r
    verifier_csrf()
    db.supprimer(article_id)
    return redirect(url_for("admin_accueil", message="Article supprimé."))


@app.route("/admin/apercu", methods=["POST"])
def admin_apercu():
    if not session.get("admin"):
        abort(403)
    verifier_csrf()
    return str(filtre_markdown(request.form.get("contenu", "")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
