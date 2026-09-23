# ViyaSave – Guide de démarrage (débutant)

Site gratuit pour télécharger des vidéos TikTok en MP4 sans filigrane.

## Contenu du projet

| Fichier | Rôle |
|---|---|
| `app.py` | Le serveur (Python/Flask). Récupère la vidéo avec **yt-dlp**. |
| `templates/index.html` | La page d'accueil (ce que voient les visiteurs). |
| `templates/conditions.html` | Les conditions d'utilisation. |
| `requirements.txt` | La liste des bibliothèques à installer. |
| `Procfile` | La commande de démarrage pour l'hébergeur. |

---

## Étape 1 – Tester sur votre ordinateur

1. Installez **Python 3.10 ou plus récent** : https://www.python.org/downloads/ (sous Windows, cochez « Add Python to PATH »).
2. Décompressez le dossier `tiktok-downloader`, puis ouvrez un terminal dedans.
3. Tapez :
   ```
   pip install -r requirements.txt
   python app.py
   ```
4. Ouvrez votre navigateur sur **http://localhost:5000** et collez un lien TikTok.

## Étape 2 – Mettre le site en ligne gratuitement (Render)

1. Créez un compte sur **https://github.com** et créez un nouveau dépôt (« New repository »).
2. Envoyez-y tous les fichiers du projet (bouton « Add file » → « Upload files »).
3. Créez un compte sur **https://render.com** (connexion avec GitHub).
4. Cliquez sur **New → Web Service** et choisissez votre dépôt.
5. Réglages :
   - **Runtime** : Python
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2`
   - **Plan** : Free
6. Cliquez sur **Create Web Service**. Après quelques minutes, votre site est en ligne à une adresse du type `https://viyasave.onrender.com`.

> Le plan gratuit de Render met le site en veille après 15 minutes sans visite : la première visite suivante prend ~30 secondes à charger. C'est normal.

## Étape 3 – Entretien

- **TikTok change souvent son fonctionnement.** Si les téléchargements échouent, mettez à jour yt-dlp : sur Render, cliquez sur **Manual Deploy → Clear build cache & deploy** (la dernière version sera réinstallée).
- Remplacez `votre-email@exemple.com` dans `templates/conditions.html` par votre vraie adresse de contact.
- Pour changer le nom du site, remplacez « ViyaSave » dans les fichiers HTML.

## Blog et panel admin

- Adresse du panel : **https://viyasave.xyz/admin**
- Variables à ajouter dans Render → Environment :
  - `ADMIN_PASSWORD` : votre mot de passe admin (long et secret)
  - `SECRET_KEY` : cliquez sur **Generate** dans Render
  - `DATABASE_URL` : lien de connexion de votre base gratuite **Neon** (neon.tech), qui garde vos articles
- Sans `DATABASE_URL`, les articles seraient effacés à chaque redémarrage de Render.
- Le site génère automatiquement `/sitemap.xml` et `/robots.txt` pour Google.

## Points importants à savoir

- **Droits d'auteur** : les vidéos appartiennent à leurs créateurs. Le site affiche un avertissement demandant de ne télécharger que ses propres vidéos ou avec autorisation, et les conditions d'utilisation prévoient une adresse de contact pour les demandes de retrait. Gardez-les.
- **Conditions de TikTok** : TikTok interdit l'accès automatisé à son service. Ce type de site existe en grand nombre, mais TikTok peut bloquer l'adresse IP de votre serveur. Si cela arrive, un changement d'hébergeur ou un VPS (ex. Hetzner, OVH, ~4 €/mois) règle souvent le problème.
- **Publicité** : si vous ajoutez des publicités (Google AdSense, etc.), sachez que certaines régies refusent les sites de téléchargement de vidéos.
- Je ne suis pas juriste : si le site prend de l'ampleur, renseignez-vous auprès d'un professionnel sur la législation de votre pays.
