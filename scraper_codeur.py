from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans interface graphique
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Utiliser Chromium et ChromeDriver installés dans le conteneur
    service = Service("/usr/bin/chromedriver")  # Chemin de ChromeDriver sur Fly.io
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

# Chemin vers ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/eines/OneDrive/Bureau/chromedriver-win64/chromedriver.exe"

# Identifiants Codeur.com
EMAIL = "admin@bandmdigitalconsulting.com"
PASSWORD = "BandMdigital2@25"

# Catégories à scraper
CATEGORIES = {
    "Développement": "https://www.codeur.com/projects/c/developpement",
    "Web": "https://www.codeur.com/projects/c/web",
    "IA": "https://www.codeur.com/projects/c/ia",
    "Systèmes d'entreprise": "https://www.codeur.com/projects/c/systemes-d-entreprise",
    "Services": "https://www.codeur.com/projects/c/services"
}

# Configuration Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Mode sans interface graphique
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service(CHROMEDRIVER_PATH)

# Base de données SQLite
DB_NAME = "projects.db"

def init_db():
    """ Initialise la base de données SQLite """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            price TEXT,
            offers TEXT,
            category TEXT,
            status TEXT DEFAULT "Nouveau",
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def login_to_codeur(driver):
    """Se connecte à Codeur.com"""
    driver.get("https://www.codeur.com/users/sign_in")
    time.sleep(3)
    try:
        email_input = driver.find_element(By.ID, "user_email")
        password_input = driver.find_element(By.ID, "user_password")
        email_input.send_keys(EMAIL)
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(3)
        print(f"✅ Connexion réussie, URL après connexion : {driver.current_url}")
    except Exception as e:
        print(f"❌ Erreur lors de la connexion : {e}")

def scrape_category(driver, category, url):
    """Scrape une catégorie et retourne la liste des projets"""
    driver.get(url)
    time.sleep(3)
    print(f"📌 Scraping de la catégorie : {category}")

    try:
        titles = [title.text.strip() for title in driver.find_elements(By.CSS_SELECTOR, "a.no-underline.visited\\:text-visited")]
        links = [
            link.get_attribute("href") if link.get_attribute("href").startswith("https")
            else "https://www.codeur.com" + link.get_attribute("href")
            for link in driver.find_elements(By.CSS_SELECTOR, "a.no-underline.visited\\:text-visited")
        ]
        raw_prices = [price.text.strip() for price in driver.find_elements(By.CSS_SELECTOR, "span.whitespace-nowrap[data-controller='tooltip']")]

        prices, offers = [], []
        for price in raw_prices:
            if "€" in price or "devis" in price:
                prices.append(price)
                offers.append("Non spécifié")
            else:
                offers.append(price)
                prices.append("Non spécifié")

        projects = []
        for i in range(len(titles)):
            projects.append({
                "Titre": titles[i],
                "Lien": links[i],
                "Prix": prices[i] if i < len(prices) else "Non spécifié",
                "Offres": offers[i] if i < len(offers) else "Non spécifié",
                "Catégorie": category
            })

        return projects

    except Exception as e:
        print(f"❌ Erreur lors du scraping de {category} : {e}")
        return []

def save_projects_to_db(projects):
    """Enregistre les projets en base de données en évitant les doublons"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    new_projects_count = 0

    for project in projects:
        try:
            c.execute('''
                INSERT INTO projects (title, link, price, offers, category, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (project["Titre"], project["Lien"], project["Prix"], project["Offres"], project["Catégorie"], "Nouveau"))
            conn.commit()
            new_projects_count += 1
        except sqlite3.IntegrityError:
            pass  # Ignore si le projet existe déjà

    conn.close()
    print(f"✅ {new_projects_count} nouveaux projets ajoutés en base de données.")

def scrape_projects():
    """Effectue le scraping de toutes les catégories et retourne les projets"""
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        login_to_codeur(driver)
        all_projects = []
        for category, url in CATEGORIES.items():
            all_projects.extend(scrape_category(driver, category, url))
        save_projects_to_db(all_projects)
        print("✅ Scraping terminé et sauvegardé en BDD.")
        return all_projects
    except Exception as e:
        print(f"❌ Erreur pendant le scraping : {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    init_db()
    scrape_projects()
