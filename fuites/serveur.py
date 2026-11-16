"""Petit serveur web local (bibliothèque standard Python uniquement, rien à installer).

Il écoute seulement sur 127.0.0.1 : personne d'autre sur le réseau ne peut y accéder.
"""
from __future__ import annotations

import json
import mimetypes
import secrets
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, analyse, sources

RACINE = Path(__file__).resolve().parent.parent
WEB = RACINE / "web"
DONNEES = RACINE / "donnees"
HISTORIQUE = DONNEES / "historique.json"
MAX_HISTORIQUE = 100

_verrou = threading.Lock()

CSP = (
    "default-src 'self'; img-src 'self' data: https://xposedornot.com https://www.google.com https://*.gstatic.com; "
    "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
    "base-uri 'none'; form-action 'none'"
)


# --------------------------- historique local ------------------------------
def lire_historique() -> list[dict]:
    try:
        return json.loads(HISTORIQUE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def ecrire_historique(items: list[dict]) -> None:
    DONNEES.mkdir(exist_ok=True)
    tmp = HISTORIQUE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items[:MAX_HISTORIQUE], ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(HISTORIQUE)


def ajouter_historique(resultat: dict) -> dict:
    entree = {
        "id": secrets.token_hex(6),
        "email": resultat["email"],
        "date": resultat["date"],
        "score": resultat["note"]["score"],
        "lettre": resultat["note"]["lettre"],
        "couleur": resultat["note"]["couleur"],
        "nb_fuites": resultat["nb_fuites"],
        "nb_mdp": resultat["nb_mdp"],
        "resultat": resultat,
    }
    with _verrou:
        items = lire_historique()
        # nouvelles fuites depuis la dernière vérification de cette adresse ?
        precedent = next((i for i in items if i["email"] == resultat["email"]), None)
        if precedent:
            anciens = {f["nom"] for f in precedent["resultat"]["fuites"]}
            resultat["nouvelles"] = [f["nom"] for f in resultat["fuites"] if f["nom"] not in anciens]
            resultat["derniere_verif"] = precedent["date"]
        items.insert(0, entree)
        ecrire_historique(items)
    return entree


# ------------------------------- serveur ------------------------------------
class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "MesInfosOntFuite"
    sys_version = ""

    def log_message(self, fmt, *args):  # journal discret : jamais d'adresse e-mail dans la console
        pass

    # -- sécurité : refuse les requêtes venant d'un autre site (DNS rebinding, CSRF)
    def _hote_ok(self) -> bool:
        hote = (self.headers.get("Host") or "").split(":")[0].strip("[]").lower()
        return hote in ("127.0.0.1", "localhost", "::1")

    def _origine_ok(self) -> bool:
        origine = self.headers.get("Origin")
        if origine is None:
            return True
        return origine.split("://", 1)[-1].split(":")[0].lower() in ("127.0.0.1", "localhost")

    def _envoyer(self, code: int, corps: bytes, type_: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def _json(self, obj, code: int = 200):
        self._envoyer(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _erreur(self, message: str, code: int = 400):
        self._json({"erreur": message}, code)

    def _lire_json(self) -> dict:
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            raise ValueError
        n = int(self.headers.get("Content-Length") or 0)
        if n > 10_000:
            raise ValueError
        data = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(data, dict):
            raise ValueError
        return data

    def _garde(self) -> bool:
        if not self._hote_ok() or not self._origine_ok():
            self._erreur("Accès refusé.", HTTPStatus.FORBIDDEN)
            return False
        return True

    # ------------------------------------------------------------------ GET
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._garde():
            return
        chemin = self.path.split("?", 1)[0]
        if chemin == "/api/info":
            return self._json({"version": __version__, "demo": sources.DEMO_EMAIL})
        if chemin == "/api/historique":
            items = lire_historique()
            return self._json([{k: v for k, v in i.items() if k != "resultat"} for i in items])
        if chemin.startswith("/api/historique/"):
            ident = chemin.rsplit("/", 1)[-1]
            item = next((i for i in lire_historique() if i["id"] == ident), None)
            return self._json(item["resultat"]) if item else self._erreur("Introuvable.", 404)
        if chemin.startswith("/api/mdp/"):
            try:
                texte = sources.plage_mdp(chemin.rsplit("/", 1)[-1])
            except sources.ErreurSource as e:
                return self._erreur(str(e), 502)
            return self._envoyer(200, texte.encode(), "text/plain; charset=utf-8")
        return self._fichier(chemin)

    def _fichier(self, chemin: str):
        if chemin in ("/", ""):
            chemin = "/index.html"
        cible = (WEB / chemin.lstrip("/")).resolve()
        if WEB not in cible.parents or not cible.is_file():
            return self._erreur("Page introuvable.", 404)
        type_ = mimetypes.guess_type(cible.name)[0] or "application/octet-stream"
        if type_.startswith("text/") or type_ in ("application/javascript",):
            type_ += "; charset=utf-8"
        self._envoyer(200, cible.read_bytes(), type_)

    # ----------------------------------------------------------------- POST
    def do_POST(self):
        if not self._garde():
            return
        if self.path != "/api/verifier":
            return self._erreur("Introuvable.", 404)
        try:
            data = self._lire_json()
        except (ValueError, json.JSONDecodeError):
            return self._erreur("Requête invalide.")
        email = str(data.get("email") or "").strip().lower()
        garder = bool(data.get("historique", True))
        if not sources.email_valide(email):
            return self._erreur("Cette adresse e-mail ne semble pas valide.")
        try:
            if email == sources.DEMO_EMAIL:
                brutes, source = sources.DEMO_FUITES, "démo"
            else:
                brutes, source = sources.fuites_email(email), "XposedOrNot"
        except sources.ErreurSource as e:
            return self._erreur(str(e), 502)
        resultat = analyse.analyser(email, brutes, source)
        if garder:
            ajouter_historique(resultat)
        return self._json(resultat)

    # --------------------------------------------------------------- DELETE
    def do_DELETE(self):
        if not self._garde():
            return
        if self.path == "/api/historique":
            with _verrou:
                ecrire_historique([])
            return self._json({"ok": True})
        if self.path.startswith("/api/historique/"):
            ident = self.path.rsplit("/", 1)[-1]
            with _verrou:
                ecrire_historique([i for i in lire_historique() if i["id"] != ident])
            return self._json({"ok": True})
        return self._erreur("Introuvable.", 404)


def creer_serveur(port: int) -> ThreadingHTTPServer:
    """Essaie le port demandé, puis les suivants s'il est déjà pris."""
    derniere = None
    for p in range(port, port + 20):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Gestionnaire)
            srv.daemon_threads = True
            return srv
        except OSError as e:
            derniere = e
    raise derniere  # type: ignore[misc]
