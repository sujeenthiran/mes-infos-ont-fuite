"""Tests (bibliothèque standard uniquement) :  python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fuites import analyse, serveur, sources  # noqa: E402


class TestAnalyse(unittest.TestCase):
    def test_aucune_fuite_note_A(self):
        r = analyse.analyser("a@b.fr", [], "test")
        self.assertEqual(r["note"]["score"], 100)
        self.assertEqual(r["note"]["lettre"], "A")
        self.assertTrue(r["plan"])  # des conseils même sans fuite

    def test_traduction_et_gravite(self):
        f = analyse.normaliser_fuite({"breach": "X", "xposed_data": "Email addresses;Passwords;Weird thing",
                                      "password_risk": "plaintext", "xposed_date": "2024"}, 2026)
        noms = [d["fr"] for d in f["donnees"]]
        self.assertEqual(noms[0], "Mots de passe")
        self.assertIn("Weird thing", noms)
        self.assertTrue(f["mot_de_passe_expose"])
        self.assertEqual(f["gravite"], 4)
        self.assertEqual(f["risque_mdp"]["libelle"], "en clair")

    def test_demo_note_basse_et_plan(self):
        r = analyse.analyser("demo@exemple.fr", sources.DEMO_FUITES, "démo")
        self.assertEqual(r["nb_fuites"], 5)
        self.assertEqual(r["nb_mdp"], 3)
        self.assertLess(r["note"]["score"], 35)
        ids = [a["id"] for a in r["plan"]]
        self.assertIn("2fa", ids)
        self.assertIn("sms", ids)
        self.assertIn("iban", ids)
        self.assertEqual(r["plan"][0]["priorite"], "urgent")

    def test_extraire_format_xon(self):
        vide = {"BreachMetrics": None, "ExposedBreaches": None, "BreachesSummary": {"site": ""}}
        self.assertEqual(sources.extraire_fuites(vide), [])
        plein = {"ExposedBreaches": {"breaches_details": [{"breach": "A"}, "bizarre"]}}
        self.assertEqual(sources.extraire_fuites(plein), [{"breach": "A"}])

    def test_email_valide(self):
        self.assertTrue(sources.email_valide("jean.dupont+test@exemple.fr"))
        for mauvais in ("", "pas-un-mail", "a@b", "a b@c.fr", "x@y.z"):
            self.assertFalse(sources.email_valide(mauvais), mauvais)


class TestServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        serveur.DONNEES = Path(cls.tmp.name)
        serveur.HISTORIQUE = serveur.DONNEES / "historique.json"
        cls.srv = serveur.creer_serveur(18765)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.tmp.cleanup()

    def req(self, chemin, data=None, methode=None, entetes=None):
        corps = json.dumps(data).encode() if data is not None else None
        h = {"Content-Type": "application/json", **(entetes or {})}
        r = urllib.request.Request(self.base + chemin, data=corps, headers=h, method=methode)
        try:
            with urllib.request.urlopen(r, timeout=5) as rep:
                return rep.status, rep.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_page_et_securite(self):
        code, corps = self.req("/")
        self.assertEqual(code, 200)
        self.assertIn(b"Mes infos ont fuit", corps)
        self.assertEqual(self.req("/../fuites/serveur.py")[0], 404)
        self.assertEqual(self.req("/api/info", entetes={"Host": "evil.com"})[0], 403)
        self.assertEqual(self.req("/api/verifier", {"email": "demo@exemple.fr"}, entetes={"Origin": "https://evil.com"})[0], 403)

    def test_demo_et_historique(self):
        code, corps = self.req("/api/verifier", {"email": "demo@exemple.fr"})
        self.assertEqual(code, 200)
        r = json.loads(corps)
        self.assertEqual(r["source"], "démo")
        code, corps = self.req("/api/verifier", {"email": "demo@exemple.fr"})
        self.assertEqual(json.loads(corps)["nouvelles"], [])
        histo = json.loads(self.req("/api/historique")[1])
        self.assertGreaterEqual(len(histo), 2)
        self.assertNotIn("resultat", histo[0])
        detail = json.loads(self.req("/api/historique/" + histo[0]["id"])[1])
        self.assertEqual(detail["email"], "demo@exemple.fr")
        self.assertEqual(self.req("/api/historique", methode="DELETE")[0], 200)
        self.assertEqual(json.loads(self.req("/api/historique")[1]), [])

    def test_email_invalide(self):
        self.assertEqual(self.req("/api/verifier", {"email": "nope"})[0], 400)

    def test_prefixe_invalide(self):
        self.assertEqual(self.req("/api/mdp/ZZZZZ")[0], 502)


if __name__ == "__main__":
    unittest.main()
