<div align="center">

# 🕵️ Mes infos ont fuité ?

**Tape ton adresse e-mail : l'outil te dit dans quelles fuites de données elle apparaît, ce que les pirates savent sur toi, et quoi faire, étape par étape.**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Aucune dépendance](https://img.shields.io/badge/d%C3%A9pendances-aucune-22c55e)
![Windows | macOS | Linux](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-ok-8b5cf6)
![Licence MIT](https://img.shields.io/badge/licence-MIT-green)

<img src="docs/capture-resultat.png" width="780" alt="Résultat d'une vérification">

</div>

---

## 🚀 Lancer l'outil (1 minute)

1. Télécharge le projet : bouton vert **Code ▸ Download ZIP** (puis décompresse), ou :
   ```bash
   git clone https://github.com/sujeenthiran/mes-infos-ont-fuite.git
   ```
2. Double-clique sur le fichier de ton système :

| Système | Fichier à lancer |
|---|---|
| 🪟 Windows | **`Lancer.bat`** |
| 🍎 macOS | **`Lancer-Mac.command`** (clic droit ▸ Ouvrir la première fois) |
| 🐧 Linux | **`./lancer.sh`** |

La page s'ouvre toute seule dans ton navigateur. C'est tout.

> Il faut Python 3.8 ou plus. Sur Windows, s'il manque, `Lancer.bat` propose de l'installer pour toi (gratuit, officiel). **Aucune autre installation**, aucun `pip install`.

---

## ✨ Ce que ça fait

| | |
|---|---|
| 📧 **Vérifier un e-mail** | Cherche ton adresse dans plus de 900 fuites connues (Canva, LinkedIn, Deezer…). |
| 🧩 **Expliquer en français simple** | Pour chaque donnée volée (mot de passe, téléphone, IBAN, date de naissance…) : ce que ça veut dire et quoi faire. |
| 🅰️ **Note de A à E** | Selon la gravité des données, la protection des mots de passe et l'âge des fuites. |
| ✅ **Plan d'action personnalisé** | Urgent → important → conseil, avec cases à cocher et liens officiels (cybermalveillance.gouv.fr, 33700…). |
| 👨‍👩‍👧 **Mode famille** | Vérifie jusqu'à 5 adresses d'un coup. |
| 🔑 **Tester un mot de passe** | A-t-il déjà fuité ? Combien de temps pour le casser ? **Il ne quitte jamais ton PC.** |
| 🎲 **Générateur de phrase de passe** | Ex. `Girafe-Piano-42-Nuage-Velo` : solide et facile à retenir. |
| 🛡️ **10 bons réflexes** | Une liste à cocher pour se protéger, même en cas de fuite. |
| 🕓 **Historique + alerte « nouvelle fuite »** | Revérifie dans 3 mois : l'outil te montre ce qui est nouveau. |
| 🖨️ **Rapport PDF** | Bouton « Imprimer / PDF » pour garder ou envoyer le rapport. |

<p align="center">
  <img src="docs/capture-mot-de-passe.png" width="390" alt="Test d'un mot de passe">
  <img src="docs/capture-reflexes.png" width="390" alt="Les bons réflexes">
</p>

👉 Exemple de rapport : [`docs/exemple-rapport.pdf`](docs/exemple-rapport.pdf). Pour essayer sans ta vraie adresse, clique sur **« Essayer avec un exemple »**.

---

## 🔒 Vie privée

- L'outil tourne **sur ton ordinateur** (`127.0.0.1`). Personne d'autre sur le réseau ne peut l'ouvrir.
- **Aucun compte, aucune publicité, aucun pistage.** Le code est ouvert : tu peux tout vérifier.
- **E-mail** : envoyé uniquement au service public [XposedOrNot](https://xposedornot.com) pour la recherche.
- **Mot de passe** : ton navigateur calcule son empreinte SHA-1 et n'envoie que les **5 premiers caractères** à [Have I Been Pwned](https://haveibeenpwned.com/Passwords) (méthode du *k-anonymat*, avec bourrage). La comparaison se fait chez toi.
- **Historique** : dans le dossier `donnees/` de l'outil, sur ton PC. Bouton « Tout effacer » dans l'onglet Historique.

## ⚠️ Limites (honnêtement)

- Aucune base n'est complète : **« aucune fuite trouvée » ne veut pas dire « aucun risque »**. Le bouton « Double-vérifier sur Have I Been Pwned » permet de croiser.
- Le service gratuit XposedOrNot limite à **25 recherches par heure** et 100 par jour. Les résultats sont gardés 1 h en mémoire pour économiser ce quota.
- L'outil ne peut pas dire *quel* mot de passe a fuité, seulement *sur quel site*.

---

## 🛠️ Pour les curieux

```
mes_infos_ont_fuite.py   point d'entrée (ouvre le navigateur)
fuites/serveur.py        mini serveur web (bibliothèque standard Python)
fuites/sources.py        appels XposedOrNot et Have I Been Pwned
fuites/analyse.py        traduction, gravité, note, plan d'action
web/                     page web (HTML, CSS, JavaScript sans framework)
tests/                   tests :  python -m unittest discover -s tests -v
```

Options : `python mes_infos_ont_fuite.py --port 9000 --sans-navigateur`

Sécurité du serveur local : écoute seulement sur `127.0.0.1`, contrôle des en-têtes `Host` et `Origin` (anti DNS-rebinding et CSRF), Content-Security-Policy stricte, aucune donnée affichée sans échappement.

## 🙏 Merci

- [XposedOrNot](https://xposedornot.com) pour l'API gratuite de recherche de fuites.
- [Have I Been Pwned](https://haveibeenpwned.com) (Troy Hunt) pour Pwned Passwords.
- [Cybermalveillance.gouv.fr](https://www.cybermalveillance.gouv.fr) pour les fiches réflexes.

Licence MIT.
