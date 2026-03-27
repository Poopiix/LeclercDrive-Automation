# 🛒 Automatisation Leclerc Drive

Ce projet est un script Python utilisant **Playwright** pour automatiser la commande d'articles sur le site Leclerc Drive. Il lit une liste de courses depuis un fichier texte, recherche les produits, applique des filtres de sélection intelligents et ajoute les articles au panier.

## 📋 Fonctionnalités
* **Recherche automatisée :** Parcourt une liste d'articles définie par l'utilisateur.
* **Règle "Bio" :** Ajoute automatiquement "Bio Village" à la recherche si le mot "bio" est détecté dans l'article.
* **Sélection intelligente :** Récupère les 4 résultats les plus pertinents, puis sélectionne le 2ème article le moins cher (ou le 1er s'il n'y a qu'un seul choix).
* **Gestion des erreurs :** Continue l'exécution même si un article n'est pas trouvé et consigne l'erreur dans un fichier journal (`articles_manquants.log`).
* **Rapport par Email :** Envoie un récapitulatif par email à la fin de l'exécution contenant uniquement les articles qui ont échoué.
* **Anti-Bot :** Conserve la session active (cookies, magasin) dans un dossier local et masque le WebDriver pour éviter les blocages du site.

---

## 🛠️ Prérequis

Assurez-vous d'avoir installé [Python 3.8+](https://www.python.org/downloads/) sur votre machine.

### Installation des dépendances

1. Ouvrez votre terminal et installez les paquets Python requis :
   ```bash
   pip install playwright python-dotenv

2. Installez le navigateur Chromium pour Playwright :
   ```bash
   playwright install chromium

⚙️ Configuration
Avant de lancer le script, vous devez créer deux fichiers à la racine du projet, au même niveau que leclercdrive.py.

1. Le fichier .env (Identifiants et Email)
Créez un fichier nommé exactement .env et complétez-le avec vos informations :

```
LECLERC_USER=votre_email_leclerc@domaine.com
LECLERC_PASS=votre_mot_de_passe_leclerc
EMAIL_SENDER=votre_email_envoi@gmail.com
EMAIL_PASSWORD=votre_mot_de_passe_application
EMAIL_RECEIVER=votre_email_reception@domaine.com
```

⚠️ Note pour Gmail (EMAIL_PASSWORD) : > Si vous utilisez un compte Gmail pour envoyer les emails, vous ne pouvez pas utiliser votre mot de passe classique. Vous devez générer un "Mot de passe d'application" (16 caractères) dans les paramètres de sécurité de votre compte Google (la validation en deux étapes doit être activée).

2. Le fichier liste.txt (Liste de courses)
Créez un fichier nommé liste.txt. Ajoutez un article par ligne.

*Exemple*
liquide vaisselle
riz Basmati Bio
pattes macaroni Turini
mouchoir en papier

🚀 Utilisation

1. Lancez le script depuis votre terminal :
```Bash
python leclercdrive.py```
```

2. Le navigateur va s'ouvrir. Une pause de 10 secondes est prévue au lancement.
Lors de la première exécution, profitez de cette pause pour accepter les cookies, vous connecter manuellement à votre compte Leclerc et choisir votre magasin Drive.
Pour les exécutions suivantes, la session sera mémorisée dans le dossier leclerc_session et vous serez déjà connecté.

3. Laissez le script tourner. Vous pouvez suivre l'avancée directement dans la console.


📂 Fichiers générés
`leclerc_session/`: Dossier créé automatiquement par Playwright pour sauvegarder votre session (cookies, cache). Ne le supprimez pas si vous voulez rester connecté entre chaque lancement.
`articles_manquants.log` : Fichier texte généré automatiquement en cas d'erreur. Il répertorie la date, l'heure et la raison de l'échec pour chaque article non trouvé.

