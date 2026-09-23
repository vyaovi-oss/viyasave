"""
Stockage des articles du blog.
- En ligne : base PostgreSQL gratuite (Neon) via la variable DATABASE_URL.
- Sur votre ordinateur : fichier local articles.db (SQLite), automatiquement.
"""
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
POSTGRES = DATABASE_URL.startswith("postgres")

if POSTGRES:
    import psycopg
    from psycopg.rows import dict_row


def _connect():
    if POSTGRES:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    conn = sqlite3.connect(os.environ.get("SQLITE_PATH", "articles.db"))
    conn.row_factory = sqlite3.Row
    return conn


def _q(sql):
    """Adapte les paramètres ? au format PostgreSQL (%s)."""
    return sql.replace("?", "%s") if POSTGRES else sql


def _run(sql, params=(), fetch=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(_q(sql), params)
        result = None
        if fetch == "one":
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetch == "all":
            result = [dict(r) for r in cur.fetchall()]
        conn.commit()
        return result
    finally:
        conn.close()


def init():
    id_col = "SERIAL PRIMARY KEY" if POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _run(f"""
        CREATE TABLE IF NOT EXISTS articles (
            id {id_col},
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            image TEXT DEFAULT '',
            published INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    # Ajout de la colonne "lang" (fr / en) si elle n'existe pas encore
    try:
        _run("ALTER TABLE articles ADD COLUMN lang TEXT DEFAULT 'fr'")
    except Exception:
        pass


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(texte):
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte[:80] or "article"


def _slug_unique(base, ignore_id=None):
    slug, n = base, 2
    while True:
        row = _run("SELECT id FROM articles WHERE slug = ?", (slug,), fetch="one")
        if not row or row["id"] == ignore_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


def lister(publies_seulement=True, limite=None, lang=None):
    sql = "SELECT * FROM articles"
    conditions, params = [], []
    if publies_seulement:
        conditions.append("published = 1")
    if lang:
        conditions.append("COALESCE(lang, 'fr') = ?")
        params.append(lang)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"
    if limite:
        sql += f" LIMIT {int(limite)}"
    lignes = _run(sql, tuple(params), fetch="all")
    for l in lignes:
        l["lang"] = l.get("lang") or "fr"
    return lignes


def _avec_lang(row):
    if row:
        row["lang"] = row.get("lang") or "fr"
    return row


def par_slug(slug):
    return _avec_lang(_run("SELECT * FROM articles WHERE slug = ?", (slug,), fetch="one"))


def par_id(article_id):
    return _avec_lang(_run("SELECT * FROM articles WHERE id = ?", (article_id,), fetch="one"))


def creer(titre, description, contenu, image, publie, slug="", lang="fr"):
    slug = _slug_unique(slugify(slug or titre))
    now = _now()
    _run(
        "INSERT INTO articles (slug, title, description, content, image, published, created_at, updated_at, lang) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (slug, titre, description, contenu, image, 1 if publie else 0, now, now, lang),
    )
    return slug


def modifier(article_id, titre, description, contenu, image, publie, slug="", lang="fr"):
    slug = _slug_unique(slugify(slug or titre), ignore_id=article_id)
    _run(
        "UPDATE articles SET slug = ?, title = ?, description = ?, content = ?, image = ?, "
        "published = ?, updated_at = ?, lang = ? WHERE id = ?",
        (slug, titre, description, contenu, image, 1 if publie else 0, _now(), lang, article_id),
    )
    return slug


def supprimer(article_id):
    _run("DELETE FROM articles WHERE id = ?", (article_id,))
