"""Sources de données publiques et gratuites.

- XposedOrNot (https://xposedornot.com) : fuites connues pour une adresse e-mail. Gratuit, sans clé.
- Have I Been Pwned « Pwned Passwords » : mots de passe compromis, par k-anonymat.
  Seuls les 5 premiers caractères de l'empreinte SHA-1 partent sur Internet.
  Le calcul de l'empreinte est fait dans ton navigateur : le mot de passe ne quitte jamais ton PC.
"""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from urllib.parse import quote

UA = "MesInfosOntFuite/1.0 (+outil local open source)"
TIMEOUT = 20

XON_ANALYTICS = "https://api.xposedornot.com/v1/breach-analytics?email={}"
HIBP_RANGE = "https://api.pwnedpasswords.com/range/{}"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-']+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PREFIXE_RE = re.compile(r"^[0-9A-F]{5}$")


class ErreurSource(Exception):
    """Erreur lisible par un humain (en français)."""


def email_valide(email: str) -> bool:
    return bool(email) and len(email) <= 254 and bool(EMAIL_RE.match(email))


def _contexte_ssl() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:  # certifi si présent (certains Python Windows/Mac n'ont pas les certificats système)
        import certifi  # type: ignore
        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx


def _get(url: str, entetes: dict | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(entetes or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_contexte_ssl()) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        corps = e.read() if hasattr(e, "read") else b""
        return e.code, corps
    except ssl.SSLError as e:
        raise ErreurSource("Connexion sécurisée impossible (certificat). Mets Python à jour ou installe le paquet « certifi ».") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErreurSource("Pas de connexion Internet, ou le service ne répond pas. Réessaie dans un instant.") from e


# Petit cache en mémoire : évite de gaspiller le quota gratuit (25 recherches / heure).
_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_SECONDES = 3600


def fuites_email(email: str) -> list[dict]:
    """Renvoie la liste brute des fuites (format breach-analytics de XposedOrNot)."""
    email = email.strip().lower()
    if not email_valide(email):
        raise ErreurSource("Cette adresse e-mail ne semble pas valide.")
    maintenant = time.time()
    if email in _cache and maintenant - _cache[email][0] < CACHE_SECONDES:
        return _cache[email][1]

    code, corps = _get(XON_ANALYTICS.format(quote(email, safe="@")))
    if code == 429:
        raise ErreurSource("Trop de recherches d'un coup : le service gratuit limite à 25 par heure. Réessaie plus tard.")
    if code == 404:
        _cache[email] = (maintenant, [])
        return []
    if code >= 400:
        raise ErreurSource(f"Le service de vérification a répondu une erreur ({code}). Réessaie plus tard.")
    try:
        data = json.loads(corps or b"{}")
    except ValueError as e:
        raise ErreurSource("Réponse illisible du service de vérification.") from e
    fuites = extraire_fuites(data)
    _cache[email] = (maintenant, fuites)
    return fuites


def extraire_fuites(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    exp = data.get("ExposedBreaches")
    if not isinstance(exp, dict):
        return []
    details = exp.get("breaches_details") or []
    return [d for d in details if isinstance(d, dict)]


def plage_mdp(prefixe: str) -> str:
    """Renvoie la liste « SUFFIXE:NOMBRE » de HIBP pour ce préfixe SHA-1 (avec bourrage anti-espionnage)."""
    prefixe = prefixe.strip().upper()
    if not PREFIXE_RE.match(prefixe):
        raise ErreurSource("Préfixe invalide.")
    code, corps = _get(HIBP_RANGE.format(prefixe), {"Add-Padding": "true", "Accept": "text/plain"})
    if code >= 400:
        raise ErreurSource(f"Le service des mots de passe a répondu une erreur ({code}).")
    return corps.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# Mode démo : fausses données pour essayer l'outil sans Internet.
# Adresse : demo@exemple.fr
# ---------------------------------------------------------------------------
DEMO_EMAIL = "demo@exemple.fr"
DEMO_FUITES = [
    {"breach": "Canva", "domain": "canva.com", "industry": "Information Technology", "xposed_date": "2019",
     "xposed_records": 137272116, "password_risk": "hardtocrack", "verified": "Yes",
     "xposed_data": "Email addresses;Geographic locations;Names;Passwords;Usernames",
     "details": "En mai 2019, le site de graphisme Canva a subi une fuite touchant 137 millions de comptes."},
    {"breach": "Deezer", "domain": "deezer.com", "industry": "Entertainment", "xposed_date": "2019",
     "xposed_records": 229037936, "password_risk": "unknown", "verified": "Yes",
     "xposed_data": "Dates of birth;Email addresses;Genders;Geographic locations;IP addresses;Names;Spoken languages;Usernames",
     "details": "Fin 2022, une sauvegarde de 2019 du service de musique Deezer a été publiée."},
    {"breach": "LinkedIn", "domain": "linkedin.com", "industry": "Social Media", "xposed_date": "2012",
     "xposed_records": 164611595, "password_risk": "easytocrack", "verified": "Yes",
     "xposed_data": "Email addresses;Passwords",
     "details": "En 2012, LinkedIn a été piraté. Les mots de passe, mal protégés (SHA-1 sans sel), ont presque tous été retrouvés."},
    {"breach": "Free", "domain": "free.fr", "industry": "Telecom", "xposed_date": "2024",
     "xposed_records": 19000000, "password_risk": "unknown", "verified": "Yes",
     "xposed_data": "Bank account numbers;Dates of birth;Email addresses;Names;Phone numbers;Physical addresses",
     "details": "En octobre 2024, l'opérateur Free a confirmé le vol de données de 19 millions d'abonnés, dont des IBAN."},
    {"breach": "Wattpad", "domain": "wattpad.com", "industry": "Entertainment", "xposed_date": "2020",
     "xposed_records": 268765495, "password_risk": "hardtocrack", "verified": "Yes",
     "xposed_data": "Bios;Dates of birth;Email addresses;Genders;IP addresses;Names;Passwords;Usernames",
     "details": "En 2020, la plateforme de lecture Wattpad a été piratée et ses données mises en vente."},
]
