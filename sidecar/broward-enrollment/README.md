# Sidecar `broward-enrollment`

Inscription automatique sur le portail Broward Dual Enrollment via nodriver + CapSolver (reCAPTCHA v2), puis configuration du mot de passe Broward depuis Outlook.

## Prérequis

- Python 3.14.5
- Google Chrome ou Chromium
- Clé API CapSolver (variable `CAPSOLVER_API_KEY` ou Paramètres Alyvo)

## Build

```bash
cd alyvo-edu-software
npm run sidecar:build:broward
```

## Test CLI

```powershell
$env:CAPSOLVER_API_KEY = "CAP-..."
python main.py --account-json '{"accountId":1,"firstName":"John","lastName":"Doe","birthday":"2000-01-12","email":"test@outlook.com"}'
```

Le payload complet doit aussi contenir `password` (mot de passe Outlook), utilise ensuite pour `New Password` et `Confirm New Password` Broward :

```powershell
python main.py --account-json '{"accountId":1,"firstName":"John","lastName":"Doe","birthday":"2000-01-12","email":"test@outlook.com","password":"OutlookPass1!"}'
```

## Constantes

- URL : `https://broward.my.site.com/dualenrollment/TX_CommunitiesSelfReg?...`
- Forgot password : `https://broward.my.site.com/dualenrollment/TX_ForgotPassword`
- Outlook entry : `https://www.microsoft.com/fr-fr/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook?deeplink=%2Fmail%2F&sdf=0`
- Site key reCAPTCHA : `6Lf5Gq8bAAAAAC3lTeW2iPoEkegr_8Xlc4TxbeKD`

## Flux complet

1. Préinscription Broward : formulaire + CapSolver.
2. Confirmation attendue : `Thank you for registering!`
3. Demande d'email : page `TX_ForgotPassword`, **1 passe** `Request Password` (sans attente initiale).
4. Ouverture page Microsoft Outlook, clic/suivi du CTA `Se connecter`.
5. Connexion Outlook avec email + mot de passe Outlook si nécessaire.
6. Recherche du mail `Set your Broward College Application Password`. Si toujours absent a la **10e** tentative (`10/90`), **1 passe** supplementaire sur `TX_ForgotPassword` puis reconnexion Outlook, puis poursuite de la recherche.
7. Clic du dernier mail Broward dans Outlook, puis extraction du lien `ForgotPasswordInterstitial`.
8. Soumission native de la page `Reset Password`; si Salesforce renvoie `URL No Longer Exists` / redirection portail sans formulaire, une nouvelle demande `Request Password` est faite puis un nouveau lien Outlook est récupéré.
9. Remplissage `New Password` et `Confirm New Password` avec le mot de passe Outlook.
10. Clic `Save Password`.
11. Portail `TargetX_Base__Portal` : clic `Start a New Application`.
12. Page « New Application » : naissance US = `Yes` (defaut), attente chargement Angular des termes, terme = premier libelle contenant `Summer`, `Start Application` (select via `selectedIndex` + digest Angular).
13. Section « Helpful Tips » : radio `I'm ready to begin`, puis `Continue`.
14. Sections Apply2 : Personal Information, Contact Information, Immigration Information, Emergency Contact, High School Details, Additional Information, `Review Application`, `Submit Your Application`, puis page `Verify & Submit` (case `I verify all is true and correct`, signature, `Verify & Submit`).

Champs optionnels dans `account-json` : `bornInUs` (defaut `Yes`), `applicationTerm` (defaut `Summer`, correspondance partielle sur le libelle, ex. `Summer 2026`), `street`, `city`, `postalCode`, `mobilePhone`, `homePhone` (defaut vide), `ssn` (sinon derive de `479412330` avec 1 chiffre modifie selon `accountId`), `emergencyFirstName`, `emergencyLastName`, `emergencyRelationship`, `emergencyMobilePhone`, `gender`, `race`, `primaryLanguage`, `highSchoolDegree`, `highSchoolGraduationDate` (defaut `2030-05-05`), `highSchoolState` (defaut `Texas`), `highSchoolName` (defaut `El Paso High School`).

Profil Apply2 par defaut (aligne sur candidature acceptee) : adresse El Paso TX 79936, genre Female, diplome prevu 2030, lycée Texas, « I visited your school ».

## reCAPTCHA (CapSolver + TargetX Broward)

Flux réel de la page (inspect DOM) :

1. `div.g-recaptcha` avec `data-callback="recaptcha"`
2. `recaptcha(token)` appelle la fonction globale **`callback(token)`** (script jQuery en bas de page)
3. `callback` fait `$("input[id$=tokenValue]").val(token)` et `$("input[id$=submit]").prop('disabled', false)`

CapSolver fournit le token ; **pas besoin de cocher la case** si `callback(token)` s’exécute.
La case peut rester vide visuellement.

Le sidecar attend jQuery + `callback` + `recaptcha`, injecte le token, puis appelle `callback(token)` et le repli jQuery.

Repli manuel : 60 s pour cocher « Je ne suis pas un robot » si Submit reste grisé (sauf erreur **Proxy IP banned** CapSolver).

Si CapSolver renvoie **Proxy IP banned by target service**, le sidecar ferme Chrome et relance **une fois** l'inscription complete pour le meme compte (2 tentatives au total).

**nodriver** : toutes les lectures JS utilisent `return_by_value=True` et `JSON.stringify` pour les objets (sinon `evaluate returned non-dict` et injection vide).
