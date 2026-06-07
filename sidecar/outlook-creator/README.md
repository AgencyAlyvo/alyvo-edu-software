# Outlook creator sidecar

Binaire PyInstaller (`--onefile`) embarquant Python + nodriver.

## Prérequis build

- Python 3.14.5
- `pip install -r requirements.txt` (nodriver 0.50.3, pyinstaller 6.20.0)

## Listes de noms US

Prénoms et noms de famille : `data/us_first_names.txt` et `data/us_last_names.txt` (5000 entrées chacun), embarqués dans le binaire au build. Pour régénérer : `node sidecar/outlook-creator/scripts/generate-name-lists.mjs`

## Build local

```bash
npm run sidecar:build
```

Produit `src-tauri/binaries/outlook-creator-{TARGET_TRIPLE}` (`.exe` sur Windows).

Le nom du fichier doit correspondre au triple Rust de la machine (`rustc --print host-tuple`).

## Runtime (dev et production)

- **Windows** : `ipconfig /flushdns` avant Chrome (app desktop : VPN puis flush ; CLI seul : flush dans le sidecar sauf `--skip-dns-flush`).
- **Chrome ou Chromium** installé sur le poste de l'utilisateur (nodriver pilote le navigateur local).
- Aucun mode simulé : le sidecar lance toujours nodriver.
- Flux automatise : `signup.live.com/?lic=1` → email → mot de passe → date de naissance → nom → CAPTCHA (appui long) → bouton **OK** (`#StickyFooter`) sur l'écran de confirmation.
- CAPTCHA : appui **13 s** sur « Appuyer et maintenir » (`humanCaptchaIframe`). Windows : souris OS réelle en priorité ; sinon CDP. PerimeterX peut quand même refuser (score anti-bot) → **15 s** laissées pour saisie manuelle en cas d'échec.
- En dev : builder le sidecar une fois (`npm run sidecar:build`) avant `npm run desktop:run:dev`.

## Dépannage

- **« Sidecar produced no output »** : le binaire a planté avant d'émettre le JSON (souvent nodriver + Python 3.14). Relancer `npm run sidecar:build` (le script applique un correctif d'encodage sur `nodriver/cdp/network.py`).
- Tester le binaire à la main :
  `src-tauri/binaries/outlook-creator-x86_64-pc-windows-msvc.exe --birthday=2008-01-12 --used-names='[["John","Doe"]]'`
  (`--password` optionnel : généré automatiquement si omis ; l'app Tauri en envoie un par compte.)
  Si le mot de passe commence par `-`, utiliser la forme `--password=-VotreMotDePasse` (avec `=`), sinon argparse le confond avec une option.
  La dernière ligne stdout doit être du JSON `{"ok":true,...}`.
