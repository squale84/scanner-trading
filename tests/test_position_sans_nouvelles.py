"""Test ciblé : une position qui ne reçoit plus de mise à jour est marquée « sans nouvelles depuis … » (index.html), jamais clôturée ni chiffrée.

Sans Neon, sans serveur, sans réseau, sans écriture : la fonction de formatage est extraite du fichier et exécutée par Node (le test est ignoré, et le dit, si Node
est absent) ; le reste est un contrôle statique du gabarit.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
echecs = []


def verifier(nom, condition, detail=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {nom}" + (f" -- {detail}" if (not condition and detail) else ""))
    if not condition:
        echecs.append(nom)


m = re.search(r"// <formatDureeSansNouvelles>\n(.*?)// </formatDureeSansNouvelles>", HTML.replace("\r\n", "\n"), re.S)
verifier("1. la fonction de formatage est présente et repérable", m is not None)
node = shutil.which("node")
if m and node:
    cas = [0, 4, 12, 59, 59.6, 60, 65, 125, 1439, 1440, 1500, 5400, 5700, None, "abc", -5]
    attendu = ["0 min", "4 min", "12 min", "59 min", "1 h 00", "1 h 00", "1 h 05", "2 h 05", "23 h 59", "1 j 0 h", "1 j 1 h", "3 j 18 h", "3 j 23 h", "0 min", "0 min", "0 min"]
    with tempfile.TemporaryDirectory() as tmp:
        chemin = os.path.join(tmp, "f.js")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(m.group(1) + f"\nconsole.log(JSON.stringify({json.dumps(cas)}.map(formatDureeSansNouvelles)));\n")
        sortie = subprocess.run([node, chemin], capture_output=True, text=True, timeout=30, encoding="utf-8")
    obtenu = json.loads(sortie.stdout) if sortie.returncode == 0 else sortie.stderr
    verifier("2. durées lues en minutes / heures / jours (AVAX figé : 5 400 min = 3 j 18 h)", obtenu == attendu, f"{obtenu}")
else:
    print("[SKIP] 2. Node absent : formatage non exécuté")

verifier("3. seuils : 12 min pour l'avertissement, 60 min pour « suivi interrompu »",
         "const SEUIL_SANS_NOUVELLES_MIN = 12;" in HTML and "const SUIVI_INTERROMPU_MIN = 60;" in HTML)
verifier("4. le gabarit de la carte utilise le formatage et le libellé « sans nouvelles depuis »",
         "sans nouvelles depuis ${formatDureeSansNouvelles(ageMin)}" in HTML and "aucune mise à jour depuis ${Math.round(ageMin)} min" not in HTML)
verifier("5. « suivi interrompu : résultat indisponible » (jamais de résultat estimé) et style d'alerte dédié",
         "suivi interrompu : résultat indisponible" in HTML and ".pos-note.stale-long" in HTML)
verifier("6. les positions de test locales ne sont jamais marquées", "const stale = !pos.isTest && ageMin !== null && ageMin > SEUIL_SANS_NOUVELLES_MIN;" in HTML)
verifier("7. le marquage se rafraîchit chaque minute (renderOpenPositions)", "setInterval(renderOpenPositions, 60 * 1000)" in HTML)

if node:
    blocs = re.findall(r"<script>(.*?)</script>", HTML, re.S)
    with tempfile.TemporaryDirectory() as tmp:
        ok = True
        for i, bloc in enumerate(blocs):
            chemin = os.path.join(tmp, f"b{i}.js")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(bloc)
            r = subprocess.run([node, "--check", chemin], capture_output=True, text=True, timeout=60, encoding="utf-8")
            if r.returncode != 0:
                ok = False
                print(r.stderr[:500])
    verifier("8. la syntaxe JavaScript de chaque bloc <script> de index.html est valide", ok and len(blocs) > 0)

if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S) : " + " ; ".join(echecs))
    sys.exit(1)
print("\nTOUT PASSE : position sans nouvelles")
