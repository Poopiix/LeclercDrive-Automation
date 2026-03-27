import os
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Chargement des variables d'environnement
load_dotenv()

LECLERC_USER = os.getenv("LECLERC_USER")
LECLERC_PASS = os.getenv("LECLERC_PASS")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def log_error(item_name, reason):
    """Enregistre les erreurs dans le fichier log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("articles_manquants.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {item_name} : {reason}\n")

def send_email(missing_items):
    """Envoie un email récapitulatif des articles manquants."""
    if not missing_items:
        return

    subject = "Leclerc Drive - Articles manquants"
    body = "Voici la liste des articles qui n'ont pas pu être ajoutés à votre panier :\n\n"
    for item in missing_items:
        body += f"- {item}\n"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email récapitulatif envoyé avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

def main():
    # 1. Lecture de la liste
    try:
        with open("liste.txt", "r", encoding="utf-8") as f:
            articles = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Erreur : Le fichier 'liste.txt' est introuvable.")
        return

    missing_items = []

    # 2. Configuration Playwright
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./leclerc_session",
            headless=False,
            channel="chrome",
            slow_mo=1500,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Ouverture du site Leclerc Drive...")
        page.goto("https://www.leclercdrive.fr/")
        
        print("Pause de 10 secondes pour vérification manuelle et connexion si besoin...")
        time.sleep(10)

        # 3. Parcours des articles
        for item in articles:
            try:
                # Règle "Bio"
                search_query = item
                if "bio" in item.lower():
                    search_query += " Bio Village"

                print(f"Recherche de : {search_query}")

                # SÉLECTEUR CORRIGÉ: On inclut 'Product' (vrais articles de la page) et 'Produit' (articles du panier)
                css_produits_valides = "[class*='Product'], [class*='Produit']"

                # ANTI-RACE-CONDITION: On repère les résultats de l'ancienne recherche présents à l'écran
                old_cards = page.locator(css_produits_valides).filter(
                    has=page.locator("[class*='PrixUnitairePartieEntiere']")
                )
                old_card_to_wait = old_cards.first if old_cards.count() > 0 else None

                # Nouvelle recherche
                search_input = page.locator('input[id*="rechercheTexte"]')
                search_input.fill("") 
                search_input.press_sequentially(search_query, delay=100)
                page.locator('input[id*="rechercheBouton"]').click()
                
                # ANTI-RACE-CONDITION: On attend la destruction de l'ancienne recherche par le site (Requête AJAX)
                if old_card_to_wait:
                    try:
                        old_card_to_wait.wait_for(state="detached", timeout=5000)
                    except Exception:
                        pass # Si le timeout survient, on continue tout de même
                
                # On filtre et on attend l'apparition des nouveaux résultats
                product_cards = page.locator(css_produits_valides).filter(
                    has=page.locator("[class*='PrixUnitairePartieEntiere']")
                )
                
                try:
                    product_cards.first.wait_for(state="visible", timeout=10000)
                except Exception:
                    raise Exception("Aucun produit avec un prix n'est apparu ou temps dépassé.")

                count = product_cards.count()
                if count == 0:
                    raise Exception("Aucun produit ne correspond à la recherche.")

                # 4 & 5. Extraction et tri
                products_data = []
                for i in range(count):
                    card = product_cards.nth(i)
                    try:
                        # Utilisation de .first.inner_text() pour éviter les erreurs "strict mode" si plusieurs prix sont barrés
                        ent_str = card.locator("[class*='PrixUnitairePartieEntiere']").first.inner_text(timeout=1000)
                        dec_str = card.locator("[class*='PrixUnitairePartieDecimale']").first.inner_text(timeout=1000)
                        
                        ent_clean = ent_str.strip().replace(' ', '').replace(',', '')
                        dec_clean = dec_str.strip().replace(' ', '').replace(',', '')
                        
                        price = float(f"{ent_clean}.{dec_clean}")
                        products_data.append({'index': i, 'price': price, 'locator': card})
                    except Exception:
                        continue
                        
                if not products_data:
                    raise Exception("Impossible de lire les prix des produits trouvés.")

                # CORRECTION : On ne conserve que les 4 premiers résultats de la recherche 
                # (les plus pertinents selon le moteur de Leclerc) avant d'appliquer la règle de prix.
                top_relevant_products = products_data[:4]

                # Tri croissant par prix uniquement sur ce top 4
                top_relevant_products.sort(key=lambda x: x['price'])
                
                # Sélection (2ème moins cher parmi le top 4 si dispo)
                target_idx = 1 if len(top_relevant_products) >= 2 else 0
                selected_product = top_relevant_products[target_idx]
                
                # Ajout au panier
                selected_product['locator'].locator(".aWCRS310_Add").click(force=True)
                print(f"-> Ajouté : {item} (Prix: {selected_product['price']}€)")
                
                time.sleep(2) # Pause de sécurité pour l'animation d'ajout
                
            except Exception as e:
                error_msg = str(e).split('\n')[0]
                log_error(item, error_msg)
                missing_items.append(item)
                print(f"-> ÉCHEC pour '{item}' : {error_msg}")

        context.close()

    # 6. Finalisation
    if missing_items:
        send_email(missing_items)
        print(f"\nScript terminé. {len(missing_items)} article(s) manquant(s). Email envoyé.")
    else:
        print("\nSuccès total ! Tous les articles ont été ajoutés au panier. (Aucun email envoyé)")

if __name__ == "__main__":
    main()