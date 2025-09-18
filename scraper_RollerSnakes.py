# Importa le librerie
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import re
import os

# Configura Selenium per l'ambiente locale
options = Options()
options.add_argument('--headless')  # Senza interfaccia grafica (opzionale)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-extensions')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')

# Rimuovi la firma di automazione
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

def initialize_driver():
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Errore durante l'inizializzazione del driver: {e}")
        return None

driver = initialize_driver()
if not driver:
    print("Impossibile inizializzare il driver. Uscita.")
    exit()

# Step 1: Accedi alla pagina principale dei prodotti
base_url = "https://eu.rollersnakes.com/collections/skates"  
driver.get(base_url)

# Aspetta che i prodotti si carichino
try:
    WebDriverWait(driver, 7).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'collection__main'))  
    )
except Exception as e:
    print(f"Errore durante l'attesa dei prodotti: {e}")
    driver.quit()
    exit()

# Step 2: Determina il numero totale di pagine
total_pages = 1
try:
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagination_elems = soup.find_all('a', class_='pagination__link')
    page_numbers = []
    if pagination_elems:
        # Cerca in ogni elemento l'attributo aria-label con "Go to page" seguito da un numero
        for elem in pagination_elems:
            aria_label = elem.get('aria-label', '')
            page_match = re.search(r'Go to page\s*(\d+)', aria_label, re.IGNORECASE)
            if page_match:
                page_numbers.append(int(page_match.group(1)))
        if page_numbers:
            total_pages = max(page_numbers)
            print(f"Trovate {total_pages} pagine totali.")
        else:
            print("Nessun indicatore di paginazione trovato. Assumo una sola pagina.")
    else:
        print("Nessun elemento di paginazione trovato. Assumo una sola pagina.")
except Exception as e:
    print(f"Errore durante la determinazione delle pagine: {e}")

# Step 3: Raccogli i link dei prodotti da tutte le pagine
product_links = []
max_retries = 3

for page_number in range(1, total_pages + 1):
    retry_count = 0
    success = False
    current_url = f"{base_url}?page={page_number}"

    while retry_count < max_retries and not success:
        try:
            print(f"Caricamento pagina: {current_url} (Pagina {page_number})")
            driver.get(current_url)

            # Aspetta che i prodotti si carichino
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'collection__main'))  
            )

            # Estrai i link dei prodotti
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            product_container = soup.find('div', class_='collection__main') 
            if product_container:
                product_titles = product_container.find_all('div', class_='product-card__info')
                product_items = [title.find('a') for title in product_titles if title.find('a')]
            else:
                print(f"Contenitore non trovato per {current_url}, cerco direttamente i prodotti")
                product_items = soup.find_all('a', href=True) 

            # Filtra i link dei prodotti
            for item in product_items:
                href = item.get('href')
                if href and '/products/' in href: 
                    full_url = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    if full_url not in product_links:
                        product_links.append(full_url)

            print(f"Pagina {page_number} - Trovati {len(product_links)} prodotti finora.")
            success = True

        except Exception as e:
            retry_count += 1
            print(f"Errore durante lo scraping di {current_url} (tentativo {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                print("Riprovo...")
                time.sleep(5)
                try:
                    driver.quit()
                except:
                    pass
                driver = initialize_driver()
                if not driver:
                    print("Impossibile riavviare il driver. Uscita.")
                    exit()
            else:
                print(f"Massimo numero di tentativi raggiunto per {current_url}. Passo alla pagina successiva.")
                break

    if not success:
        print(f"Fine scraping per la pagina {page_number} a causa di errori.")
        break

    time.sleep(2)

print(f"Trovati {len(product_links)} link di prodotti unici.")

def extract_product_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_data = {}

    # Trova tutti gli elementi del breadcrumb
    breadcrumb_items = soup.find_all('li', class_='breadcrumb__list-item')

    # Inizializza la categoria e la sottocategoria come "Unknown"
    category = "Unknown"
    subcategory = "Unknown"

    # Verifica che ci siano almeno due elementi nel breadcrumb
    if len(breadcrumb_items) >= 2:
        category = breadcrumb_items[-2].text.strip()
        subcategory = breadcrumb_items[-1].text.strip()

    # Salva i dati nel dizionario
    product_data['category'] = category
    product_data['subcategory'] = subcategory

    # Dizionario dei brand
    brand_dict = {
        'air waves': 'Air Waves',
        'anarchy': 'Anarchy',
        'bauer': 'Bauer',
        'chaya': 'Chaya',
        'cib': 'CIB',
        'clouds': 'Clouds',
        'derby laces': 'Derby Laces',
        'echo skates': 'Echo Skates',
        'gawds': 'Gawds',
        'ground_control': 'Ground Control',
        'impala': 'Impala',
        'kizer': 'Kizer',
        'luminous wheels': 'Luminous Wheels',
        'mesmer skates': 'Mesmer Skates',
        'mindless': 'Mindless',
        'moxi': 'Moxi',
        'playlife': 'Playlife',
        'playmaker': 'Playmaker',
        'powerslide': 'Powerslide',
        'razors': 'Razors',
        'rio roller': 'Rio Roller',
        'roces': 'Roces',
        'rollerblade': 'Rollerblade',
        'rollerbones': 'Rollerbones',
        'rookie': 'Rookie',
        'sfr': 'SFR',
        'shoestring': 'Shoestring',
        'sims': 'Sims',
        'skatelife': 'Skatelife',
        'supreme': 'Supreme',
        'sure grip': 'Sure Grip',
        'them skates': 'Them Skates',
        'undercover': 'Undercover',
        'usd': 'USD'
    }

    # Nome prodotto
    product_name_h1 = soup.find('h1', class_='product-title h3')
    product_name = product_name_h1.text.strip().lower() if product_name_h1 else ''

    # Estrai il brand confrontando con il dizionario
    brand = None
    for key in brand_dict:
        if key.lower() in product_name:
            brand = brand_dict[key]
            break
    product_data['brand'] = brand if brand else 'Unknown'

    # Descrizione prodotto
    description_div = soup.find('div', class_='prose')
    product_data['description'] = description_div.text.strip() if description_div else None

    # ID prodotto (SKU)
    id_div = soup.find(class_='variant-sku')
    if id_div:
        id_text = id_div.text.strip()
        id_alpha_numeric = re.search(r'SKU[:\s]*([a-zA-Z0-9\-]+)', id_text, re.IGNORECASE)
        product_data['id'] = id_alpha_numeric.group(1) if id_alpha_numeric else None
    else:
        product_data['id'] = None

    # Prezzo corrente
    price_div = soup.find('div', class_='product-info__block-item', attrs={'data-block-id': 'price'})
    if price_div:
        price_span = price_div.find('sale-price', class_='h4 text-subdued')
        if price_span:
            price_text = price_span.text.strip()
            cleaned_price = re.sub(r'[^\d.,]', '', price_text).replace(',', '.')
            if cleaned_price and re.match(r'^-?\d*\.?\d+$', cleaned_price):
                try:
                    price_numeric = float(cleaned_price)
                    product_data['price(€)'] = price_numeric
                except ValueError:
                    product_data['price(€)'] = None
            else:
                product_data['price(€)'] = None
        else:
            product_data['price(€)'] = None
    else:
        product_data['price(€)'] = None

    # Disponibilità
    inventory_div = soup.find(class_='inventory')
    if inventory_div:
        inventory_text = inventory_div.text.strip()
        product_data['availability'] = inventory_text if inventory_text else None
    else:
        product_data['availability'] = None

    # Valutazione/5
    rating_div = soup.find('div', class_='jdgm-prev-badge')
    if rating_div and 'data-average-rating' in rating_div.attrs:
        rating_text = rating_div['data-average-rating'].strip('"').strip()
        if rating_text and re.match(r'^-?\d*\.?\d+$', rating_text):
            try:
                score_numeric = float(rating_text)
                product_data['score/5'] = score_numeric
            except ValueError:
                product_data['score/5'] = None
        else:
            product_data['score/5'] = None
    else:
        product_data['score/5'] = None

    # Numero recensioni
    review_div = soup.find('div', class_='jdgm-prev-badge')
    if review_div and 'data-number-of-reviews' in review_div.attrs:
        review_text = review_div['data-number-of-reviews'].strip('"').strip()
        if review_text and re.match(r'^\d+$', review_text):
            try:
                review_numeric = int(review_text)
                product_data['num_reviews'] = review_numeric
            except ValueError:
                product_data['num_reviews'] = None
        else:
            product_data['num_reviews'] = None
    else:
        product_data['num_reviews'] = None

    # Link prodotto
    product_data['product_link'] = driver.current_url

    # Aggiungi data e ora dell'estrazione
    product_data['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return product_data

# Step 4: Per ogni prodotto, estrai i dati e salvali in una lista
all_products = []
for product_url in product_links:
    print(f"Scraping prodotto: {product_url}")
    try:
        driver.get(product_url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-info__block-list'))  
        )

        product_data = extract_product_data(driver)
        if product_data:
            all_products.append(product_data)
            print(f"Elaborato: {product_url}")
        else:
            print(f"Impossibile estrarre i dati per {product_url}")

        time.sleep(0.5)

    except Exception as e:
        print(f"Errore durante l'elaborazione del prodotto {product_url}: {e}")
        continue

# Step 5: Salva i dati in un file JSON
if all_products:
    current_date = datetime.now().strftime('%Y-%m-%d')
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    json_dir = f'rollersnakes_products/{year}/{month}'
    json_path = f'{json_dir}/products_{current_date}.json'
    
    os.makedirs(json_dir, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)
    print(f"Salvati {len(all_products)} prodotti in {json_path}")
else:
    print("Nessun prodotto trovato da salvare.")

# Chiudi il driver
driver.quit()



