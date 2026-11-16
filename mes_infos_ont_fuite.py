#!/usr/bin/env python3
"""Mes infos ont fuité ? Lance l'outil et ouvre la page dans ton navigateur.

Usage :  python mes_infos_ont_fuite.py [--port 8765] [--sans-navigateur]
"""
import argparse
import sys
import threading
import webbrowser

if sys.version_info < (3, 8):
    sys.exit("Python 3.8 ou plus récent est nécessaire : https://www.python.org/downloads/")

# Console Windows : force l'UTF-8 pour les accents et emojis
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fuites import __version__
from fuites.serveur import creer_serveur


def main() -> None:
    p = argparse.ArgumentParser(description="Mes infos ont fuité ? (outil local)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--sans-navigateur", action="store_true", help="ne pas ouvrir le navigateur")
    args = p.parse_args()

    srv = creer_serveur(args.port)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print(f"  ║   🕵  MES INFOS ONT FUITÉ ?   v{__version__:<15}║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  ✅ C'est prêt ! La page s'ouvre dans ton navigateur : {url}")
    print("  🔒 Tout reste sur ton ordinateur (rien n'est envoyé à un serveur à nous).")
    print("  ❌ Pour arrêter : ferme cette fenêtre (ou Ctrl+C).")
    print()
    if not args.sans_navigateur:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 À bientôt !")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
