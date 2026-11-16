/* Mes infos ont fuité ? — interface (aucune dépendance externe) */
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

/* ---------- petits utilitaires ---------- */
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function sansBalises(v) {
  // DOMParser : document inerte (aucun script ni image n'est chargé)
  const doc = new DOMParser().parseFromString(String(v ?? ""), "text/html");
  doc.querySelectorAll("script,style").forEach(n => n.remove());
  return (doc.body && doc.body.textContent) || "";
}
function lienSur(url) {
  try { const u = new URL(url); return (u.protocol === "https:" || u.protocol === "http:") ? u.href : null; } catch { return null; }
}
function nombre(n) { return Number(n || 0).toLocaleString("fr-FR"); }
function grosNombre(n) {
  n = Number(n || 0);
  if (n >= 1e9) return (n / 1e9).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " milliard" + (n >= 2e9 ? "s" : "");
  if (n >= 1e6) return (n / 1e6).toLocaleString("fr-FR", { maximumFractionDigits: 0 }) + " millions";
  return nombre(n);
}
function dateFr(iso) {
  try { return new Date(iso).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" }); } catch { return iso; }
}
const stock = {
  lire(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  ecrire(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* navigation privée */ } },
};
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("voir");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("voir"), 2600);
}
async function api(url, opts = {}) {
  const r = await fetch(url, opts);
  const type = r.headers.get("content-type") || "";
  const data = type.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error((data && data.erreur) || "Erreur inattendue (" + r.status + ")");
  return data;
}

/* ---------- onglets ---------- */
function ouvrirVue(nom) {
  $$(".onglet").forEach(b => b.classList.toggle("actif", b.dataset.vue === nom));
  $$(".vue").forEach(v => v.classList.toggle("active", v.id === "vue-" + nom));
  if (nom === "historique") chargerHistorique();
  history.replaceState(null, "", "#" + nom);
}
$$(".onglet").forEach(b => b.addEventListener("click", () => ouvrirVue(b.dataset.vue)));

/* =====================================================================
   1. E-MAIL
   ===================================================================== */
let INFO = { demo: "demo@exemple.fr" };
let dernierResultat = null;

function montrer(id, oui) { $(id).classList.toggle("cache", !oui); }

async function verifierEmail(email) {
  montrer("#erreur", false); montrer("#resultat", false); montrer("#famille-resultats", false);
  montrer("#chargement", true);
  const bouton = $("#form-email button"); bouton.disabled = true;
  try {
    const res = await api("/api/verifier", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, historique: $("#garder").checked }),
    });
    afficherResultat(res);
  } catch (e) {
    $("#erreur").innerHTML = "⚠️ " + esc(e.message);
    montrer("#erreur", true);
  } finally {
    montrer("#chargement", false); bouton.disabled = false;
  }
}

$("#form-email").addEventListener("submit", e => {
  e.preventDefault();
  const email = $("#email").value.trim();
  if (email) verifierEmail(email);
});
$("#btn-demo").addEventListener("click", () => { $("#email").value = INFO.demo; verifierEmail(INFO.demo); });
$("#btn-famille").addEventListener("click", () => $("#zone-famille").classList.toggle("cache"));

$("#btn-verif-famille").addEventListener("click", async () => {
  const emails = [...new Set($("#emails-famille").value.split(/[\s,;]+/).map(s => s.trim().toLowerCase()).filter(Boolean))].slice(0, 5);
  if (!emails.length) return toast("Ajoute au moins une adresse.");
  montrer("#erreur", false); montrer("#resultat", false); montrer("#chargement", true);
  const zone = $("#famille-resultats"); zone.innerHTML = ""; montrer("#famille-resultats", true);
  const resultats = [];
  for (const email of emails) {
    try {
      const res = await api("/api/verifier", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, historique: $("#garder").checked }),
      });
      resultats.push(res);
    } catch (e) {
      resultats.push({ email, erreur: e.message });
    }
    afficherFamille(resultats);
    await new Promise(r => setTimeout(r, 700)); // le service gratuit limite à 2 requêtes / seconde
  }
  montrer("#chargement", false);
});

function afficherFamille(resultats) {
  const zone = $("#famille-resultats");
  zone.innerHTML = `<div class="carte"><h3>👨‍👩‍👧 Résultats de la famille</h3><p class="doux">Clique sur une adresse pour voir le détail et son plan d'action.</p>
    <div class="famille">${resultats.map((r, i) => r.erreur
      ? `<div class="membre"><div class="pastille-note" style="background:#64748b">?</div><div class="info"><b>${esc(r.email)}</b><span class="doux">⚠️ ${esc(r.erreur)}</span></div></div>`
      : `<div class="membre" data-i="${i}"><div class="pastille-note" style="background:${esc(r.note.couleur)}">${esc(r.note.lettre)}</div>
          <div class="info"><b>${esc(r.email)}</b><span class="doux">${r.nb_fuites ? `${r.nb_fuites} fuite${r.nb_fuites > 1 ? "s" : ""}, dont ${r.nb_mdp} avec mot de passe` : "Aucune fuite connue 🎉"}</span></div>
          <span>➜</span></div>`).join("")}</div></div>`;
  $$(".membre[data-i]", zone).forEach(m => m.addEventListener("click", () => {
    afficherResultat(resultats[+m.dataset.i]);
    $("#resultat").scrollIntoView({ behavior: "smooth" });
  }));
}

function anneau(note) {
  const r = 86, c = 2 * Math.PI * r, plein = c * note.score / 100;
  return `<div class="anneau"><svg width="200" height="200" viewBox="0 0 200 200">
      <circle cx="100" cy="100" r="${r}" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="16"/>
      <circle cx="100" cy="100" r="${r}" fill="none" stroke="${esc(note.couleur)}" stroke-width="16" stroke-linecap="round"
        stroke-dasharray="${plein} ${c}" style="filter:drop-shadow(0 0 10px ${esc(note.couleur)})"/>
    </svg><div class="valeur"><div><div class="lettre" style="color:${esc(note.couleur)}">${esc(note.lettre)}</div><div class="score">${note.score} / 100</div></div></div></div>`;
}

function logo(f) {
  const initiale = esc((f.nom || "?").charAt(0).toUpperCase());
  const src = lienSur(f.logo);
  return `<div class="fuite-logo">${src ? `<img src="${esc(src)}" alt="" loading="lazy" data-initiale="${initiale}">` : initiale}</div>`;
}

const COULEUR_NIVEAU = { 4: "var(--rouge)", 3: "var(--orange)", 2: "var(--jaune)", 1: "#64748b" };

function carteFuite(f) {
  const desc = sansBalises(f.description);
  const site = lienSur(f.site);
  return `<article class="fuite n${f.gravite}">
    <div class="fuite-tete">${logo(f)}
      <div><h4>${esc(f.nom)}</h4><div class="meta">${f.annee ? "📅 " + f.annee : ""}${f.secteur ? " · " + esc(f.secteur) : ""}${f.comptes ? " · " + grosNombre(f.comptes) + " comptes" : ""}</div></div>
      <span class="niveau" style="background:${COULEUR_NIVEAU[f.gravite]}">${esc(f.niveau)}</span></div>
    ${desc ? `<p class="desc">${esc(desc.length > 260 ? desc.slice(0, 257) + "…" : desc)}</p>` : ""}
    <div class="pastilles">${f.donnees.map(d => `<span class="pastille g${d.gravite}">${d.icone} ${esc(d.fr)}</span>`).join("")}</div>
    ${f.risque_mdp ? `<div class="mdp-risque">🔑 Mot de passe ${esc(f.risque_mdp.libelle)} : ${esc(f.risque_mdp.explication)}</div>` : ""}
    ${site ? `<div class="petit" style="margin-top:8px"><a href="${esc(site)}" target="_blank" rel="noopener noreferrer">${esc(f.domaine)} ↗</a></div>` : ""}
  </article>`;
}

function clePlan(email) { return "plan:" + email; }

function afficherResultat(res) {
  dernierResultat = res;
  const n = res.note;
  const faites = new Set(stock.lire(clePlan(res.email), []));
  let titre, phrase;
  if (!res.nb_fuites) {
    titre = "Bonne nouvelle&nbsp;! 🎉";
    phrase = "Cette adresse n'apparaît dans aucune fuite connue. Garde quand même les bons réflexes : une fuite peut arriver demain.";
  } else {
    titre = `${n.titre} : ${res.nb_fuites} fuite${res.nb_fuites > 1 ? "s" : ""} trouvée${res.nb_fuites > 1 ? "s" : ""}`;
    phrase = `Ton adresse apparaît dans ${res.nb_fuites} fuite${res.nb_fuites > 1 ? "s" : ""} de données${res.nb_mdp ? `, dont <b>${res.nb_mdp} avec ton mot de passe</b>` : ""}. Pas de panique : suis le plan d'action ci-dessous, étape par étape.`;
  }
  let bandeaux = "";
  if (res.source === "démo") bandeaux += `<div class="bandeau info">🎬 Données d'exemple : ce n'est pas une vraie vérification. Tape ta propre adresse pour un vrai résultat.</div>`;
  if (res.nouvelles && res.nouvelles.length) bandeaux += `<div class="bandeau alerte">🆕 Nouvelle${res.nouvelles.length > 1 ? "s" : ""} fuite${res.nouvelles.length > 1 ? "s" : ""} depuis ta vérification du ${esc(dateFr(res.derniere_verif))} : ${res.nouvelles.map(esc).join(", ")}</div>`;
  else if (res.derniere_verif) bandeaux += `<div class="bandeau ok">✅ Rien de nouveau depuis ta vérification du ${esc(dateFr(res.derniere_verif))}.</div>`;

  const donneesExpliquees = res.donnees.filter(d => d.explication);

  $("#resultat").innerHTML = `
    <div class="entete-rapport"><h1>🕵️ Rapport « Mes infos ont fuité ? »</h1><div>${esc(res.email)}<br><span class="doux">${esc(dateFr(res.date))}</span></div></div>
    <div class="carte">
      <div class="synthese">${anneau(n)}
        <div>
          <div class="doux petit">${esc(res.email)} · vérifié le ${esc(dateFr(res.date))}</div>
          <h2 class="titre-resultat">${titre}</h2>
          <p>${phrase}</p>
          <div class="tuiles">
            <div class="tuile"><b>${res.nb_fuites}</b><span>fuite${res.nb_fuites > 1 ? "s" : ""}</span></div>
            <div class="tuile"><b style="color:${res.nb_mdp ? "var(--rouge)" : "var(--vert)"}">${res.nb_mdp}</b><span>avec mot de passe</span></div>
            <div class="tuile"><b>${res.donnees.length}</b><span>types de données</span></div>
            <div class="tuile"><b>${res.derniere || "—"}</b><span>fuite la plus récente</span></div>
          </div>
        </div>
      </div>
      ${bandeaux}
      <div class="actions-resultat">
        <button class="btn secondaire" id="btn-imprimer">🖨️ Imprimer / PDF</button>
        <button class="btn secondaire" id="btn-aller-plan">✅ Voir mon plan d'action</button>
        <a class="btn secondaire" href="${esc(res.verifier_aussi)}" target="_blank" rel="noopener noreferrer">🔁 Double-vérifier sur Have I Been Pwned ↗</a>
      </div>
    </div>

    ${res.donnees.length ? `
    <div class="titre-section"><h3>🧩 Ce qui a fuité sur toi</h3></div>
    <div class="carte">
      <div class="pastilles">${res.donnees.map(d => `<span class="pastille g${d.gravite}" title="Gravité ${esc(d.niveau)}">${d.icone} ${esc(d.fr)}${d.fois > 1 ? ` ×${d.fois}` : ""}</span>`).join("")}</div>
      ${donneesExpliquees.length ? `<div class="explications">${donneesExpliquees.map(d => `
        <div class="explication"><div class="ico">${d.icone}</div><div><b>${esc(d.fr)}</b>
          <p>${esc(d.explication)}</p><p class="faire">👉 ${esc(d.conseil)}</p></div></div>`).join("")}</div>` : ""}
    </div>` : ""}

    <div class="titre-section" id="plan-titre"><h3>✅ Ton plan d'action</h3><span class="compte" id="plan-compte"></span></div>
    <div class="carte">
      <div class="progression"><div id="plan-barre"></div></div>
      <div class="plan">${res.plan.map(a => {
        const lien = lienSur(a.lien);
        return `<label class="action ${faites.has(a.id) ? "faite" : ""}" data-id="${esc(a.id)}">
          <input type="checkbox" ${faites.has(a.id) ? "checked" : ""}>
          <div><h4><span class="prio ${esc(a.priorite)}">${esc(a.priorite)}</span>${esc(a.titre)}</h4>
          <p>${esc(a.detail)}</p>${lien ? `<a href="${esc(lien)}" target="_blank" rel="noopener noreferrer">${esc(a.lien_texte || "En savoir plus")} ↗</a>` : ""}</div></label>`;
      }).join("")}</div>
    </div>

    ${res.fuites.length ? `
    <div class="titre-section"><h3>🗂️ Le détail des fuites</h3><span class="compte">${res.fuites.length}</span></div>
    <div class="fuites">${res.fuites.map(carteFuite).join("")}</div>` : ""}
  `;
  montrer("#resultat", true);

  $$("#resultat img[data-initiale]").forEach(img => img.addEventListener("error", () => { img.parentElement.textContent = img.dataset.initiale; }));
  $("#btn-imprimer").addEventListener("click", () => window.print());
  $("#btn-aller-plan").addEventListener("click", () => $("#plan-titre").scrollIntoView({ behavior: "smooth" }));
  $$("#resultat .action input").forEach(cb => cb.addEventListener("change", () => {
    const lab = cb.closest(".action"); lab.classList.toggle("faite", cb.checked);
    const ids = $$("#resultat .action input:checked").map(x => x.closest(".action").dataset.id);
    stock.ecrire(clePlan(res.email), ids);
    majPlan();
    if (cb.checked) toast("Bravo, une étape de faite 💪");
  }));
  majPlan();
}

function majPlan() {
  const tout = $$("#resultat .action input"), faits = tout.filter(x => x.checked).length;
  $("#plan-compte").textContent = `${faits} / ${tout.length}`;
  $("#plan-barre").style.width = (tout.length ? 100 * faits / tout.length : 0) + "%";
}

/* =====================================================================
   2. MOT DE PASSE
   ===================================================================== */
const COURANTS = new Set(("123456 123456789 12345678 password motdepasse azerty azertyuiop qwerty 111111 123123 000000 " +
  "1234567890 1234567 abc123 soleil doudou chouchou loulou marseille bonjour coucou iloveyou admin welcome " +
  "football princesse jetaime nicolas camille 654321 666666 121212 password1 qwerty123 azerty123 dragon monkey " +
  "sunshine master superman batman pokemon minecraft").split(" "));

function analyseForce(mdp) {
  if (!mdp) return null;
  let jeu = 0;
  if (/[a-z]/.test(mdp)) jeu += 26;
  if (/[A-Z]/.test(mdp)) jeu += 26;
  if (/\d/.test(mdp)) jeu += 10;
  if (/[^A-Za-z0-9]/.test(mdp)) jeu += 33;
  let bits = mdp.length * Math.log2(Math.max(jeu, 1));
  const conseils = [];
  const bas = mdp.toLowerCase();
  if (COURANTS.has(bas) || COURANTS.has(bas.replace(/[\d!.?]+$/, ""))) { bits = Math.min(bits, 10); conseils.push("C'est l'un des mots de passe les plus utilisés au monde."); }
  if (/(.)\1{2,}/.test(mdp)) { bits -= 10; conseils.push("Évite les caractères répétés (aaa, 111)."); }
  if (/(0123|1234|2345|3456|4567|5678|6789|abcd|azer|qwer|wxcv)/i.test(mdp)) { bits -= 12; conseils.push("Évite les suites (1234, abcd, azer)."); }
  if (/(19|20)\d\d/.test(mdp)) { bits -= 8; conseils.push("Évite les années (souvent une date de naissance)."); }
  if (mdp.length < 12) conseils.push("Vise au moins 12 caractères, ou mieux : une phrase de passe de 5 mots.");
  if (jeu <= 36 && mdp.length < 16) conseils.push("Mélange majuscules, chiffres et symboles, ou allonge-le.");
  bits = Math.max(0, bits);
  const secondes = Math.pow(2, bits) / 2 / 1e10; // 10 milliards d'essais par seconde (ordinateur de pirate)
  let niveau;
  if (bits < 28) niveau = { t: "Très faible", c: "var(--rouge)", p: 12 };
  else if (bits < 45) niveau = { t: "Faible", c: "var(--orange)", p: 32 };
  else if (bits < 60) niveau = { t: "Moyen", c: "var(--jaune)", p: 55 };
  else if (bits < 80) niveau = { t: "Solide", c: "#84cc16", p: 80 };
  else niveau = { t: "Excellent", c: "var(--vert)", p: 100 };
  return { bits, niveau, temps: dureeFr(secondes), conseils };
}

function dureeFr(s) {
  if (s < 1) return "moins d'une seconde";
  const u = [["siècle", 3.15e9], ["an", 3.15e7], ["mois", 2.6e6], ["jour", 86400], ["heure", 3600], ["minute", 60], ["seconde", 1]];
  if (s > 3.15e11) return "plus de 10 000 ans";
  for (const [nom, v] of u) if (s >= v) { const n = Math.floor(s / v); return n + " " + nom + (n > 1 && nom !== "mois" ? "s" : ""); }
  return "quelques secondes";
}

$("#mdp").addEventListener("input", () => {
  const a = analyseForce($("#mdp").value);
  const barre = $("#force-remplissage");
  montrer("#mdp-resultat", false);
  if (!a) { barre.style.width = "0"; $("#force-titre").textContent = "—"; $("#force-detail").textContent = ""; $("#force-conseils").innerHTML = ""; return; }
  barre.style.width = a.niveau.p + "%"; barre.style.background = a.niveau.c;
  $("#force-titre").textContent = a.niveau.t; $("#force-titre").style.color = a.niveau.c;
  $("#force-detail").textContent = `· temps pour le casser : ${a.temps}`;
  $("#force-conseils").innerHTML = a.conseils.map(c => `<li>${esc(c)}</li>`).join("");
});
$("#oeil").addEventListener("click", () => { const i = $("#mdp"); i.type = i.type === "password" ? "text" : "password"; });

async function sha1Hex(texte) {
  const octets = new TextEncoder().encode(texte);
  if (window.crypto && crypto.subtle) {
    const h = await crypto.subtle.digest("SHA-1", octets);
    return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("").toUpperCase();
  }
  return sha1Secours(octets);
}

/* SHA-1 de secours (si le navigateur ne fournit pas crypto.subtle) */
function sha1Secours(m) {
  const l = m.length, w = new Uint32Array(80);
  const n = ((l + 8) >> 6) + 1, blocs = new Uint32Array(n * 16);
  for (let i = 0; i < l; i++) blocs[i >> 2] |= m[i] << (24 - (i % 4) * 8);
  blocs[l >> 2] |= 0x80 << (24 - (l % 4) * 8);
  blocs[n * 16 - 1] = l * 8;
  let [a0, b0, c0, d0, e0] = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0];
  const rot = (x, k) => (x << k) | (x >>> (32 - k));
  for (let i = 0; i < blocs.length; i += 16) {
    for (let t = 0; t < 80; t++) w[t] = t < 16 ? blocs[i + t] : rot(w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16], 1);
    let [a, b, c, d, e] = [a0, b0, c0, d0, e0];
    for (let t = 0; t < 80; t++) {
      const f = t < 20 ? (b & c) | (~b & d) : t < 40 ? b ^ c ^ d : t < 60 ? (b & c) | (b & d) | (c & d) : b ^ c ^ d;
      const k = t < 20 ? 0x5a827999 : t < 40 ? 0x6ed9eba1 : t < 60 ? 0x8f1bbcdc : 0xca62c1d6;
      const tmp = (rot(a, 5) + f + e + k + w[t]) >>> 0;
      e = d; d = c; c = rot(b, 30) >>> 0; b = a; a = tmp;
    }
    a0 = (a0 + a) >>> 0; b0 = (b0 + b) >>> 0; c0 = (c0 + c) >>> 0; d0 = (d0 + d) >>> 0; e0 = (e0 + e) >>> 0;
  }
  return [a0, b0, c0, d0, e0].map(x => x.toString(16).padStart(8, "0")).join("").toUpperCase();
}

$("#form-mdp").addEventListener("submit", async e => {
  e.preventDefault();
  const mdp = $("#mdp").value;
  if (!mdp) return toast("Tape d'abord un mot de passe.");
  const btn = $("#form-mdp button[type=submit]"); btn.disabled = true;
  const zone = $("#mdp-resultat");
  try {
    const empreinte = await sha1Hex(mdp);
    const prefixe = empreinte.slice(0, 5), suffixe = empreinte.slice(5);
    $("#demo-hash").textContent = prefixe + " " + suffixe.slice(0, 12) + "…";
    const liste = await api("/api/mdp/" + prefixe);
    let fois = 0;
    for (const ligne of liste.split("\n")) {
      const [s, c] = ligne.trim().split(":");
      if (s === suffixe) { fois = parseInt(c, 10) || 0; break; }
    }
    const a = analyseForce(mdp);
    zone.innerHTML = fois > 0
      ? `<div class="carte" style="border-color:rgba(239,68,68,.55)"><div class="verdict"><div class="gros">🚨</div><div>
          <h3 style="color:#fca5a5">Ce mot de passe a fuité ${nombre(fois)} fois&nbsp;!</h3>
          <p>Les pirates l'ont dans leurs listes et l'essaient en premier. <b>Ne l'utilise plus nulle part</b> et change-le sur tous les sites où il sert.
          Astuce : utilise le générateur de phrase de passe juste en dessous.</p></div></div></div>`
      : `<div class="carte" style="border-color:rgba(34,197,94,.5)"><div class="verdict"><div class="gros">✅</div><div>
          <h3 style="color:#86efac">Introuvable dans les fuites connues</h3>
          <p>Bonne nouvelle. ${a && a.bits < 45 ? "Mais il reste <b>facile à deviner</b> : allonge-le." : "Garde-le pour un seul site et active la double authentification."}</p></div></div></div>`;
    montrer("#mdp-resultat", true);
  } catch (err) {
    zone.innerHTML = `<div class="carte erreur">⚠️ ${esc(err.message)}</div>`;
    montrer("#mdp-resultat", true);
  } finally { btn.disabled = false; }
});

/* Générateur de phrase de passe (mots français simples, sans accents) */
const MOTS = ("abeille abricot acrobate aigle album algue amande ananas ancre anguille antenne arbre arc argent armoire artiste astre atelier avion avocat badge baguette baleine balcon ballon bambou banane banc bateau berger biscuit bison bougie boussole bouteille bambin " +
  "brioche brosse cactus cadeau cahier camion canard canoe carotte cartable castor cerise chameau chapeau chaton chocolat citron clavier clown cobra comete concert corbeau coton crabe crayon crocodile cygne " +
  "dauphin dentelle desert diamant dinosaure domino dragon echelle eclair ecureuil elephant enigme epice escargot etoile falaise fantome farine fenetre feutre flamant flocon fontaine fourmi fraise fromage fusee " +
  "galaxie gateau gazelle geant girafe glacier gorille goudron grenouille guitare hamac hamster harpe herisson hibou horloge igloo iguane jaguar jardin jongleur journal kayak kiwi koala lampe lapin lavande " +
  "legume lezard licorne lion lune lutin machine magicien manteau marmotte marteau medaille melon meteore miroir moineau montagne moto mouette mouton nuage ocean oiseau olive orange orchestre ours " +
  "palmier panda papillon parapluie pastel pelican perroquet piano pinceau pirate planete plume poisson pomme poney potiron prairie puzzle radis raisin rameur renard requin robot rocher roseau rubis " +
  "sablier salade sapin satellite saumon savon serpent sirop soleil souris sphinx tambour tapis taupe tempete tigre tomate tortue toucan train trefle tresor tulipe valise vanille velo violon volcan wagon yaourt zebre").split(/\s+/);

function hasard(max) { const a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % max; }
function nouvellePhrase() {
  const n = +$("#nb-mots").value;
  const mots = Array.from({ length: n }, () => { const m = MOTS[hasard(MOTS.length)]; return m[0].toUpperCase() + m.slice(1); });
  mots.splice(hasard(n + 1), 0, String(hasard(90) + 10));
  $("#phrase").textContent = mots.join("-");
}
$("#btn-phrase").addEventListener("click", nouvellePhrase);
$("#nb-mots").addEventListener("change", nouvellePhrase);
$("#btn-copier").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("#phrase").textContent); toast("Copié 📋 (colle-le dans ton gestionnaire)"); }
  catch { toast("Sélectionne le texte et fais Ctrl+C"); }
});

/* =====================================================================
   3. RÉFLEXES
   ===================================================================== */
const REFLEXES = [
  ["📮", "Sécuriser ma boîte mail en premier", "C'est la clé de tous tes comptes (mot de passe oublié = e-mail). Mot de passe unique + double authentification."],
  ["🔐", "Activer la double authentification", "Sur ta boîte mail, ta banque, Amazon, tes réseaux sociaux. Préfère une appli (Google/Microsoft Authenticator) au SMS."],
  ["🗝️", "Un mot de passe différent par site", "Si un site fuit, les autres restent protégés. Le plus simple : un gestionnaire comme Bitwarden (gratuit)."],
  ["🎲", "Des phrases de passe longues", "« Girafe-Piano-42-Nuage-Velo » est plus solide et plus facile à retenir que « P@ssw0rd »."],
  ["🎣", "Ne jamais cliquer dans un SMS ou e-mail urgent", "Colis, amende, impôts, compte bloqué : va sur le site en tapant toi-même l'adresse."],
  ["📞", "Ne jamais donner un code reçu par SMS", "Aucun conseiller (banque, Ameli, opérateur) ne te le demandera. C'est toujours une arnaque."],
  ["🔄", "Mettre à jour téléphone et ordinateur", "Les mises à jour bouchent les failles. Active les mises à jour automatiques."],
  ["🧹", "Supprimer les vieux comptes", "Chaque compte oublié est une fuite possible. Fais le ménage une fois par an."],
  ["💾", "Faire des sauvegardes", "Photos et documents importants : une copie sur un disque externe ou un cloud, au cas où."],
  ["🔁", "Revérifier ici tous les 3 mois", "De nouvelles fuites sont publiées chaque semaine. L'historique te dira ce qui est nouveau."],
];
function afficherReflexes() {
  const faits = new Set(stock.lire("reflexes", []));
  $("#liste-reflexes").innerHTML = REFLEXES.map(([ico, t, d], i) => `
    <label class="reflexe ${faits.has(i) ? "fait" : ""}"><div class="ico">${ico}</div><div><h4>${esc(t)}</h4><p>${esc(d)}</p></div>
    <input type="checkbox" data-i="${i}" ${faits.has(i) ? "checked" : ""}></label>`).join("");
  const n = faits.size;
  $("#reflexes-barre").style.width = (100 * n / REFLEXES.length) + "%";
  $("#reflexes-texte").textContent = n === REFLEXES.length ? "🏆 Bravo, tu as tous les bons réflexes !" : `${n} / ${REFLEXES.length} réflexes en place`;
  $$("#liste-reflexes input").forEach(cb => cb.addEventListener("change", () => {
    const ids = $$("#liste-reflexes input:checked").map(x => +x.dataset.i);
    stock.ecrire("reflexes", ids); afficherReflexes();
  }));
}

/* =====================================================================
   4. HISTORIQUE
   ===================================================================== */
async function chargerHistorique() {
  const zone = $("#liste-historique");
  try {
    const items = await api("/api/historique");
    if (!items.length) { zone.innerHTML = `<div class="vide">Aucune vérification pour l'instant. 🕵️</div>`; return; }
    zone.innerHTML = items.map(i => `
      <div class="histo"><div class="note-histo" style="background:${esc(i.couleur)}">${esc(i.lettre)}</div>
        <div class="info"><b>${esc(i.email)}</b><span class="doux petit">${esc(dateFr(i.date))} · ${i.nb_fuites} fuite${i.nb_fuites > 1 ? "s" : ""} · ${i.score}/100</span></div>
        <button class="btn secondaire" data-voir="${esc(i.id)}">Voir</button>
        <button class="btn secondaire" data-suppr="${esc(i.id)}" title="Supprimer">🗑️</button></div>`).join("");
    $$("[data-voir]", zone).forEach(b => b.addEventListener("click", async () => {
      const res = await api("/api/historique/" + b.dataset.voir);
      ouvrirVue("email"); montrer("#famille-resultats", false); montrer("#erreur", false); afficherResultat(res);
    }));
    $$("[data-suppr]", zone).forEach(b => b.addEventListener("click", async () => {
      await api("/api/historique/" + b.dataset.suppr, { method: "DELETE" }); chargerHistorique();
    }));
  } catch (e) { zone.innerHTML = `<div class="vide">⚠️ ${esc(e.message)}</div>`; }
}
let confirmerVider = 0;
$("#btn-vider").addEventListener("click", async () => {
  if (Date.now() - confirmerVider > 3000) { confirmerVider = Date.now(); return toast("Clique encore une fois pour tout effacer"); }
  await api("/api/historique", { method: "DELETE" }); toast("Historique effacé 🗑️"); chargerHistorique();
});

/* ---------- démarrage ---------- */
(async () => {
  try { INFO = await api("/api/info"); $("#version").textContent = "v" + INFO.version; } catch { /* hors ligne */ }
  nouvellePhrase();
  afficherReflexes();
  const vue = location.hash.slice(1);
  if (["email", "mdp", "reflexes", "historique"].includes(vue)) ouvrirVue(vue);
  $("#email").focus();
})();
