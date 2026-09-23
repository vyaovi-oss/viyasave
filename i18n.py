"""Textes du site en français et en anglais."""

TEXTES = {
    "fr": {
        "lang": "fr",
        "titre_page": "ViyaSave – Télécharger des vidéos TikTok sans filigrane",
        "meta_description": "Téléchargez gratuitement vos vidéos TikTok en MP4, sans filigrane, en haute qualité.",
        "h1": "Téléchargez vos vidéos TikTok sans filigrane",
        "sous_titre": "Gratuit, rapide, en MP4 haute qualité. Aucune inscription.",
        "placeholder": "Collez le lien de la vidéo TikTok ici",
        "coller": "Coller",
        "telecharger": "Télécharger",
        "telecharger_mp4": "Télécharger le MP4",
        "miniature_alt": "Miniature de la vidéo",
        "etape1": "Ouvrez TikTok et appuyez sur « Partager » puis « Copier le lien ».",
        "etape2": "Collez le lien dans le champ ci-dessus.",
        "etape3": "Appuyez sur « Télécharger » et enregistrez la vidéo.",
        "guides": "Guides et astuces",
        "tous_articles": "Voir tous les articles →",
        "avertissement": "Téléchargez uniquement vos propres vidéos ou celles dont vous avez l'autorisation. "
                         "Respectez les droits des créateurs. ViyaSave n'est pas affilié à TikTok ni à ByteDance.",
        "blog": "Blog",
        "conditions": "Conditions d'utilisation",
        "url_conditions": "/conditions",
        "autre_langue": "English",
        "url_autre_langue": "/en",
        # Messages du navigateur
        "js_recherche": "Recherche de la vidéo…",
        "js_preparation": "Préparation du fichier… le téléchargement va démarrer.",
        "js_coller_manuel": "Collez le lien manuellement (appui long dans le champ).",
        "js_erreur": "Erreur inconnue.",
        # Messages du serveur
        "err_trop": "Trop de demandes. Réessayez dans une minute.",
        "err_lien": "Lien invalide. Collez un lien TikTok (ex : https://www.tiktok.com/@nom/video/123...).",
        "err_video": "Impossible de récupérer cette vidéo. Elle est peut-être privée ou supprimée.",
        "err_echec": "Échec du téléchargement. Réessayez plus tard.",
    },
    "en": {
        "lang": "en",
        "titre_page": "ViyaSave – TikTok Video Downloader Without Watermark",
        "meta_description": "Download TikTok videos without watermark for free. Save them as HD MP4 on iPhone, Android or PC. No app, no sign-up.",
        "h1": "Download TikTok videos without watermark",
        "sous_titre": "Free, fast, HD MP4. No sign-up required.",
        "placeholder": "Paste the TikTok video link here",
        "coller": "Paste",
        "telecharger": "Download",
        "telecharger_mp4": "Download MP4",
        "miniature_alt": "Video thumbnail",
        "etape1": "Open TikTok, tap “Share”, then “Copy link”.",
        "etape2": "Paste the link in the box above.",
        "etape3": "Tap “Download” and save the video.",
        "guides": "Guides & tips",
        "tous_articles": "See all articles →",
        "avertissement": "Only download your own videos or videos you have permission to use. "
                         "Respect creators' rights. ViyaSave is not affiliated with TikTok or ByteDance.",
        "blog": "Blog",
        "conditions": "Terms of use",
        "url_conditions": "/en/terms",
        "autre_langue": "Français",
        "url_autre_langue": "/",
        "js_recherche": "Looking for the video…",
        "js_preparation": "Preparing your file… the download will start shortly.",
        "js_coller_manuel": "Please paste the link manually (long press in the box).",
        "js_erreur": "Unknown error.",
        "err_trop": "Too many requests. Please try again in a minute.",
        "err_lien": "Invalid link. Please paste a TikTok link (e.g. https://www.tiktok.com/@name/video/123...).",
        "err_video": "Could not fetch this video. It may be private or deleted.",
        "err_echec": "Download failed. Please try again later.",
    },
}


def textes(lang):
    return TEXTES.get(lang, TEXTES["fr"])
