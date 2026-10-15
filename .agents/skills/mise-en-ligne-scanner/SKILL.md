---
name: mise-en-ligne-scanner
description: Séquence de mise en ligne du scanner — push GitHub, déploiement Render, contrôle du site en production, puis alertes TradingView. À utiliser seulement quand l'utilisateur donne explicitement son « go » pour déployer des commits déjà validés.
---

# Mise en ligne du scanner

Sans « go » explicite de l'utilisateur, ne rien pousser. Si une étape échoue, **s'arrêter** et faire le compte rendu : pas de correction improvisée en production.

## 1. Avant le push
- `git status` propre sur les fichiers concernés ; `git log origin/main..main` = exactement les commits validés.
- Aucun secret dans le diff (`git diff origin/main..main` : pas de chaîne de connexion, mot de passe, jeton).
- Variables d'environnement nouvelles : les faire créer par l'utilisateur dans Render (« Save only »), sans jamais en afficher la valeur.

## 2. GitHub
- `git push origin main`, puis noter `git rev-parse --short HEAD`.

## 3. Render
- Render redéploie automatiquement depuis `main`. Dans Render → service → *Events*, le déploiement **Live** doit porter **le même commit** que celui noté à l'étape 2. Tant que ce n'est pas le cas, le site sert l'ancienne version.
- En offre gratuite, disque éphémère : l'état vit dans Neon, pas sur le disque.

## 4. Contrôle du site
- `GET /health` : `status` = `alive`, `storage.loaded` et `storage.healthy` vrais, `unsaved_events` = 0, `reset_protected` = vrai.
- La page d'accueil servie contient bien la modification déployée (comparer un élément propre au commit avec le `index.html` local).
- Contrôles ciblés sur ce qui a changé uniquement (journal, positions, calendrier, Reset refusé sans code…). Aucune écriture de test dans Neon.

## 5. Alertes TradingView (seulement si un Pine a changé)
- Les alertes existantes restent figées sur l'ancienne version : l'utilisateur doit les **supprimer et les recréer** sur chaque actif, webhook seul.
- Vérifier ensuite que les nouvelles alertes reçues portent la nouvelle `version` (`/api/journal`).

## Compte rendu
En français : commit poussé, commit Live sur Render, résultat de chaque contrôle, actions restantes pour l'utilisateur.
