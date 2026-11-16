"""Analyse des fuites : traduction en français simple, gravité, note et plan d'action.

Tout est calculé ici, sur ton ordinateur. Rien n'est envoyé ailleurs.
"""
from __future__ import annotations

import datetime as _dt
import math
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Types de données exposées : nom anglais (source) -> (français, gravité, icône)
# gravité : 4 = critique, 3 = élevée, 2 = moyenne, 1 = faible
# ---------------------------------------------------------------------------
DONNEES: dict[str, tuple[str, int, str]] = {
    "passwords": ("Mots de passe", 4, "🔑"),
    "password hints": ("Indices de mot de passe", 3, "🔑"),
    "security questions and answers": ("Questions secrètes et réponses", 4, "❓"),
    "auth tokens": ("Jetons de connexion", 4, "🎟️"),
    "credit cards": ("Cartes bancaires", 4, "💳"),
    "credit card info": ("Cartes bancaires", 4, "💳"),
    "partial credit card data": ("Cartes bancaires (partiel)", 3, "💳"),
    "credit card cvv": ("Cryptogrammes de carte (CVV)", 4, "💳"),
    "bank account numbers": ("Numéros de compte bancaire (IBAN)", 4, "🏦"),
    "banking pins": ("Codes PIN bancaires", 4, "🏦"),
    "account balances": ("Soldes de compte", 3, "🏦"),
    "financial transactions": ("Transactions financières", 3, "🏦"),
    "social security numbers": ("Numéros de sécurité sociale", 4, "🪪"),
    "national ids": ("Numéros de pièce d'identité", 4, "🪪"),
    "government issued ids": ("Pièces d'identité", 4, "🪪"),
    "passport numbers": ("Numéros de passeport", 4, "🛂"),
    "driver's licenses": ("Permis de conduire", 4, "🪪"),
    "health insurance information": ("Infos d'assurance santé", 4, "🏥"),
    "medical records": ("Dossiers médicaux", 4, "🏥"),
    "biometric data": ("Données biométriques", 4, "🧬"),
    "private messages": ("Messages privés", 3, "💬"),
    "phone numbers": ("Numéros de téléphone", 3, "📱"),
    "physical addresses": ("Adresses postales", 3, "🏠"),
    "dates of birth": ("Dates de naissance", 3, "🎂"),
    "date of birth": ("Dates de naissance", 3, "🎂"),
    "names": ("Noms et prénoms", 2, "👤"),
    "usernames": ("Pseudos / identifiants", 2, "👤"),
    "email addresses": ("Adresses e-mail", 2, "📧"),
    "ip addresses": ("Adresses IP", 2, "🌐"),
    "geographic locations": ("Localisation", 2, "📍"),
    "social media profiles": ("Profils réseaux sociaux", 2, "📣"),
    "photos": ("Photos", 2, "🖼️"),
    "employers": ("Employeurs", 1, "🏢"),
    "job titles": ("Postes / métiers", 1, "🏢"),
    "genders": ("Genre", 1, "⚧"),
    "spoken languages": ("Langues parlées", 1, "🗣️"),
    "time zones": ("Fuseaux horaires", 1, "🕒"),
    "website activity": ("Activité sur le site", 1, "🖱️"),
    "purchases": ("Achats", 2, "🛒"),
    "device information": ("Infos sur les appareils", 1, "💻"),
    "browser user agent details": ("Infos du navigateur", 1, "💻"),
    "browser user agent info": ("Infos du navigateur", 1, "💻"),
    "education levels": ("Niveau d'études", 1, "🎓"),
    "income levels": ("Revenus", 2, "💶"),
    "marital statuses": ("Situation familiale", 1, "💍"),
    "salutations": ("Civilité", 1, "👤"),
    "ethnicities": ("Origines", 3, "🔒"),
    "religions": ("Religion", 3, "🔒"),
    "sexual orientations": ("Orientation sexuelle", 3, "🔒"),
    "family members' names": ("Noms des proches", 2, "👨‍👩‍👧"),
    "vehicle details": ("Véhicules", 1, "🚗"),
    "avatars": ("Avatars", 1, "🖼️"),
    "bios": ("Biographies de profil", 1, "📝"),
    "chat logs": ("Conversations", 3, "💬"),
}

NIVEAUX = {4: "critique", 3: "élevée", 2: "moyenne", 1: "faible"}

# Ce que veut dire une donnée exposée, et quoi faire. Clé = nom anglais en minuscules.
CONSEILS: dict[str, tuple[str, str]] = {
    "passwords": (
        "Ton mot de passe de ce site est entre les mains de pirates. Ils l'essaient automatiquement "
        "sur d'autres sites (Gmail, Amazon, banque…).",
        "Change ce mot de passe tout de suite, ainsi que partout où tu utilisais le même ou un proche.",
    ),
    "security questions and answers": (
        "Les réponses à tes questions secrètes (nom de ton animal, ville de naissance…) sont connues.",
        "Change ces réponses partout. Astuce : invente des réponses fausses et note-les dans ton gestionnaire.",
    ),
    "credit cards": (
        "Des informations de carte bancaire ont fuité.",
        "Appelle ta banque pour faire opposition et surveille tes relevés.",
    ),
    "bank account numbers": (
        "Ton IBAN a fuité. On peut s'en servir pour de faux prélèvements ou des arnaques au faux conseiller.",
        "Surveille tes prélèvements. Ta banque ne te demandera jamais un code par téléphone.",
    ),
    "phone numbers": (
        "Ton numéro peut recevoir des SMS piégés (faux colis, fausse amende, faux CPF).",
        "Ne clique jamais sur un lien reçu par SMS. Transfère les SMS suspects au 33700.",
    ),
    "physical addresses": (
        "Ton adresse est connue : courriers piégés, faux livreurs, usurpation.",
        "Méfie-toi des courriers et appels qui citent ton adresse pour paraître crédibles.",
    ),
    "dates of birth": (
        "Avec ton nom et ta date de naissance, un escroc peut se faire passer pour toi.",
        "Ne l'utilise jamais dans un mot de passe ou un code. Surveille les courriers inattendus (crédits, abonnements).",
    ),
    "social security numbers": (
        "Un numéro d'identité a fuité : risque d'usurpation d'identité.",
        "Surveille tes comptes et signale tout abus sur cybermalveillance.gouv.fr.",
    ),
    "passport numbers": (
        "Un numéro de passeport a fuité : risque d'usurpation d'identité.",
        "En cas de doute, déclare-le à la police et renouvelle le document.",
    ),
    "private messages": (
        "Des messages privés ont fuité et peuvent servir au chantage.",
        "Si quelqu'un te fait du chantage, ne paie pas et appelle le 17 ou signale sur pharos.gouv.fr.",
    ),
    "email addresses": (
        "Ton adresse e-mail est connue : tu peux recevoir plus de spam et d'hameçonnage.",
        "Méfie-toi des e-mails urgents qui te demandent de te connecter ou de payer.",
    ),
    "ip addresses": (
        "Ton adresse IP de l'époque a fuité. Elle permet de deviner ta ville.",
        "Pas d'action urgente. Une IP de box change souvent.",
    ),
}

RISQUE_MDP = {
    "plaintext": ("en clair", "Les mots de passe étaient stockés EN CLAIR : lisibles immédiatement.", 4),
    "easytocrack": ("facile à casser", "Les mots de passe étaient mal protégés : faciles à retrouver.", 3),
    "hardtocrack": ("bien protégé", "Les mots de passe étaient bien chiffrés, mais un mot de passe faible reste devinable.", 2),
    "unknown": ("inconnu", "On ne sait pas comment les mots de passe étaient protégés.", 3),
}

INDUSTRIES = {
    "Entertainment": "Divertissement", "Information Technology": "Informatique",
    "Social Media": "Réseau social", "Retail": "Commerce", "Gaming": "Jeux vidéo",
    "Education": "Éducation", "Financial": "Finance", "Health": "Santé",
    "Healthcare": "Santé", "Government": "Administration", "Travel": "Voyage",
    "Telecom": "Télécom", "Food": "Alimentation", "Dating": "Rencontres",
    "Electronics": "Électronique", "Media": "Médias", "Miscellaneous": "Divers",
    "Software": "Logiciel", "Internet": "Internet", "Sports": "Sport",
}


def _cle(nom: str) -> str:
    return nom.strip().lower()


def traduire_donnee(nom: str) -> dict:
    fr, grav, ico = DONNEES.get(_cle(nom), (nom.strip(), 1, "📄"))
    return {"en": nom.strip(), "fr": fr, "gravite": grav, "niveau": NIVEAUX[grav], "icone": ico}


def _annee(valeur) -> int | None:
    if valeur is None:
        return None
    s = str(valeur).strip()
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4])
    return None


def normaliser_fuite(b: dict, annee_courante: int | None = None) -> dict:
    """Transforme une fuite brute (format XposedOrNot breach-analytics) en fiche lisible."""
    annee_courante = annee_courante or _dt.date.today().year
    brut = b.get("xposed_data") or ""
    if isinstance(brut, list):
        noms = [str(x) for x in brut]
    else:
        noms = [x for x in str(brut).split(";") if x.strip()]
    donnees = sorted((traduire_donnee(n) for n in noms), key=lambda d: -d["gravite"])
    # dédoublonne sur le libellé français
    vus, uniques = set(), []
    for d in donnees:
        if d["fr"] not in vus:
            vus.add(d["fr"])
            uniques.append(d)

    risque_cle = str(b.get("password_risk") or "unknown").lower().replace("_", "")
    mdp_expose = any(_cle(d["en"]) in ("passwords", "password hints") for d in uniques)
    risque = RISQUE_MDP.get(risque_cle, RISQUE_MDP["unknown"]) if mdp_expose else None

    annee = _annee(b.get("xposed_date"))
    age = (annee_courante - annee) if annee else None
    grav_max = max((d["gravite"] for d in uniques), default=1)
    if risque and risque[2] == 4:
        grav_max = 4

    # Points perdus pour cette fuite (sert à la note globale)
    points = {4: 22, 3: 12, 2: 6, 1: 3}[grav_max]
    if mdp_expose:
        points += {4: 10, 3: 6, 2: 2}.get(risque[2], 4)
    if age is not None:
        if age <= 2:
            points = int(points * 1.4)
        elif age >= 10:
            points = int(points * 0.6)

    domaine = (b.get("domain") or "").strip()
    nom = (b.get("breach") or b.get("name") or "Inconnu").strip()
    logo = (b.get("logo") or "").strip()
    if logo and not logo.startswith("http"):
        logo = "https://xposedornot.com/static/logos/" + logo

    return {
        "nom": nom,
        "domaine": domaine,
        "site": f"https://{domaine}" if domaine else "",
        "annee": annee,
        "age": age,
        "comptes": int(b.get("xposed_records") or 0),
        "secteur": INDUSTRIES.get(str(b.get("industry") or ""), b.get("industry") or ""),
        "description": (b.get("details") or "").strip(),
        "logo": logo,
        "verifiee": str(b.get("verified", "")).lower() in ("yes", "true", "1"),
        "donnees": uniques,
        "mot_de_passe_expose": mdp_expose,
        "risque_mdp": {"cle": risque_cle, "libelle": risque[0], "explication": risque[1]} if risque else None,
        "gravite": grav_max,
        "niveau": NIVEAUX[grav_max],
        "points": points,
    }


def calculer_note(fuites: list[dict]) -> dict:
    # décroissance douce : chaque fuite pèse, sans tomber à 0 dès 4 ou 5 fuites
    perdus = sum(f["points"] for f in fuites)
    score = round(100 * math.exp(-perdus / 75))
    if not fuites:
        score = 100
    if score >= 90:
        lettre, titre, couleur = "A", "Très bien protégé", "#22c55e"
    elif score >= 75:
        lettre, titre, couleur = "B", "Plutôt bien", "#84cc16"
    elif score >= 55:
        lettre, titre, couleur = "C", "À surveiller", "#eab308"
    elif score >= 35:
        lettre, titre, couleur = "D", "Exposé", "#f97316"
    else:
        lettre, titre, couleur = "E", "Très exposé", "#ef4444"
    return {"score": score, "lettre": lettre, "titre": titre, "couleur": couleur}


def plan_action(fuites: list[dict]) -> list[dict]:
    """Plan d'action personnalisé, du plus urgent au moins urgent."""
    actions: list[dict] = []

    def ajouter(id_, priorite, titre, detail, lien=None, lien_texte=None):
        if any(a["id"] == id_ for a in actions):
            return
        actions.append({"id": id_, "priorite": priorite, "titre": titre, "detail": detail,
                        "lien": lien, "lien_texte": lien_texte})

    # 1) Changer les mots de passe des sites touchés (les plus récents d'abord)
    avec_mdp = sorted((f for f in fuites if f["mot_de_passe_expose"]),
                      key=lambda f: -(f["annee"] or 0))
    for f in avec_mdp:
        urg = "urgent" if (f["risque_mdp"] and f["risque_mdp"]["cle"] in ("plaintext", "easytocrack")) or (f["age"] is not None and f["age"] <= 3) else "important"
        ajouter(
            f"mdp-{f['nom']}", urg,
            f"Changer le mot de passe {f['nom']}",
            f"Fuite de {f['annee'] or 'date inconnue'} ({f['risque_mdp']['libelle'] if f['risque_mdp'] else '?'}). "
            "Change-le aussi sur tous les sites où tu utilisais le même. Si tu n'utilises plus ce compte, supprime-le.",
            f["site"] or None, f"Aller sur {f['domaine']}" if f["domaine"] else None,
        )

    types = {_cle(d["en"]) for f in fuites for d in f["donnees"]}
    if avec_mdp:
        ajouter("2fa", "urgent", "Activer la double authentification (2FA)",
                "Commence par ta boîte mail, puis banque, Amazon, réseaux sociaux. Même avec ton mot de passe, "
                "un pirate ne pourra pas entrer sans le code reçu sur ton téléphone.",
                "https://www.cybermalveillance.gouv.fr/tous-nos-contenus/fiches-reflexes/double-authentification",
                "Guide officiel 2FA")
        ajouter("gestionnaire", "important", "Utiliser un gestionnaire de mots de passe",
                "Un mot de passe différent pour chaque site, sans rien retenir. Bitwarden est gratuit et open source.",
                "https://bitwarden.com/fr-fr/", "Découvrir Bitwarden")
    if types & {"credit cards", "credit card info", "credit card cvv", "partial credit card data"}:
        ajouter("banque", "urgent", "Prévenir ta banque",
                "Une carte bancaire a fuité : fais opposition si elle est encore valide et surveille tes relevés.",
                "https://www.service-public.fr/particuliers/vosdroits/F2004", "Que faire (service-public.fr)")
    if "bank account numbers" in types:
        ajouter("iban", "important", "Surveiller tes prélèvements",
                "Ton IBAN a fuité. Vérifie chaque mois qu'aucun prélèvement inconnu n'apparaît.", None, None)
    if "phone numbers" in types:
        ajouter("sms", "important", "Te méfier des SMS et appels",
                "Faux colis, fausse amende, faux conseiller bancaire : ne clique jamais et ne donne aucun code. "
                "Transfère les SMS d'arnaque au 33700.",
                "https://www.33700.fr/", "Signaler un SMS (33700)")
    if types & {"dates of birth", "date of birth", "physical addresses", "social security numbers",
                "passport numbers", "national ids", "government issued ids"}:
        ajouter("identite", "important", "Surveiller l'usurpation d'identité",
                "Assez d'infos ont fuité pour se faire passer pour toi. Surveille les courriers inattendus "
                "(crédit, abonnement, amende). En cas de problème, dépose plainte.",
                "https://www.cybermalveillance.gouv.fr/tous-nos-contenus/fiches-reflexes/usurpation-identite",
                "Fiche réflexe usurpation")
    if "security questions and answers" in types:
        ajouter("questions", "urgent", "Changer tes questions secrètes",
                "Change les réponses partout. Astuce : réponds par des mots inventés que tu ranges dans ton gestionnaire.",
                None, None)
    if types & {"private messages", "chat logs", "photos", "sexual orientations"}:
        ajouter("chantage", "important", "Savoir réagir à un chantage",
                "Si quelqu'un menace de publier tes messages ou photos : ne paie jamais, garde les preuves, signale-le.",
                "https://www.internet-signalement.gouv.fr/", "Signaler (Pharos)")
    if fuites:
        ajouter("phishing", "conseil", "Reconnaître l'hameçonnage",
                "Ton e-mail circule chez les pirates. Méfie-toi des messages urgents, des fautes, des liens raccourcis. "
                "Dans le doute, va sur le site en tapant toi-même l'adresse.",
                "https://www.cybermalveillance.gouv.fr/tous-nos-contenus/fiches-reflexes/hameconnage-phishing",
                "Fiche réflexe hameçonnage")
        ajouter("vieux-comptes", "conseil", "Supprimer les comptes que tu n'utilises plus",
                "Moins de comptes = moins de fuites. Cherche « supprimer mon compte » sur les vieux sites.",
                None, None)
        ajouter("alerte", "conseil", "Être prévenu des prochaines fuites",
                "Inscris ton adresse au service d'alerte gratuit de Have I Been Pwned.",
                "https://haveibeenpwned.com/NotifyMe", "S'abonner aux alertes")
    else:
        ajouter("2fa", "conseil", "Activer la double authentification (2FA)",
                "Aucune fuite connue, bravo. La 2FA te protège même si une fuite arrive demain.",
                "https://www.cybermalveillance.gouv.fr/tous-nos-contenus/fiches-reflexes/double-authentification",
                "Guide officiel 2FA")
        ajouter("gestionnaire", "conseil", "Utiliser un gestionnaire de mots de passe",
                "Un mot de passe unique par site : si un site fuit, les autres restent protégés.",
                "https://bitwarden.com/fr-fr/", "Découvrir Bitwarden")
        ajouter("alerte", "conseil", "Être prévenu des prochaines fuites",
                "Inscris ton adresse au service d'alerte gratuit de Have I Been Pwned.",
                "https://haveibeenpwned.com/NotifyMe", "S'abonner aux alertes")

    ordre = {"urgent": 0, "important": 1, "conseil": 2}
    actions.sort(key=lambda a: ordre[a["priorite"]])
    return actions


def resume_donnees(fuites: list[dict]) -> list[dict]:
    """Quelles données ont fuité au total (pour les pastilles), avec explication."""
    compte: dict[str, dict] = {}
    for f in fuites:
        for d in f["donnees"]:
            c = compte.setdefault(d["fr"], {**d, "fois": 0, "explication": None, "conseil": None})
            c["fois"] += 1
            if c["explication"] is None and _cle(d["en"]) in CONSEILS:
                c["explication"], c["conseil"] = CONSEILS[_cle(d["en"])]
    return sorted(compte.values(), key=lambda d: (-d["gravite"], -d["fois"]))


def analyser(email: str, brutes: list[dict], source: str) -> dict:
    fuites = [normaliser_fuite(b) for b in brutes]
    fuites.sort(key=lambda f: (-f["gravite"], -(f["annee"] or 0)))
    note = calculer_note(fuites)
    return {
        "email": email,
        "date": _dt.datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "nb_fuites": len(fuites),
        "nb_mdp": sum(1 for f in fuites if f["mot_de_passe_expose"]),
        "premiere": min((f["annee"] for f in fuites if f["annee"]), default=None),
        "derniere": max((f["annee"] for f in fuites if f["annee"]), default=None),
        "note": note,
        "fuites": fuites,
        "donnees": resume_donnees(fuites),
        "plan": plan_action(fuites),
        "verifier_aussi": f"https://haveibeenpwned.com/account/{quote(email)}",
    }
