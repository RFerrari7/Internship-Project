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
options.add_argument('--headless')  
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-extensions')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
#options.add_argument('--blink-settings=imagesEnabled=false')
#options.add_argument('--disable-application-cache')
#options.add_argument('--disable-cache')
#options.add_argument('--disk-cache-size=0')

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

# Step 1: Accedi alla pagina principale per sport rotellistici
categories_url = "https://www.decathlon.it/tutti-gli-sport/roller"
driver.get(categories_url)

# Aspetta che le categorie si carichino
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'shelf__cards'))
    )
except Exception as e:
    print(f"Errore durante l'attesa delle categorie: {e}")
    driver.quit()
    exit()

# Estrai i link e i nomi delle categorie (macro-categorie)
soup = BeautifulSoup(driver.page_source, 'html.parser')
category_links_with_name = []  # Lista di tuple (link_categoria, nome_categoria)
category_names = soup.find_all('div', class_='category-card__name')
category_items = [name.find('a') for name in category_names if name.find('a')]

excluded_category = ["Marchi pattinI", "Pattini in linea e 4 ruote"]

for item in category_items:
    href = item.get('href')
    if href:
        full_url = href if href.startswith('http') else f"https://www.decathlon.it{href}"
        # Filtra solo i link delle categorie principali
        if '/tutti-gli-sport/roller/' in full_url and full_url.count('/') == 5:
            # Estrai il nome della categoria dal testo dell'elemento
            category_name = item.text.strip() if item.text else "Unknown"
            # Normalizzazione aggiuntiva
            category_name = " ".join(category_name.split())
            # Escludo la categoria superflua
            if category_name not in excluded_category:
            # Evita duplicati
                if not any(full_url == link for link, _ in category_links_with_name):
                    category_links_with_name.append((full_url, category_name))

print(f"Trovate {len(category_links_with_name)} categorie (macro-categorie).")

# Step 2: Per ogni categoria, estrai i link dei prodotti (tutte le pagine)
product_links_with_macro = []  # Lista di tuple (link_prodotto, macro_categoria)
max_retries = 3  # Numero massimo di tentativi per ogni categoria

for category_url, macro_category in category_links_with_name:
    print(f"Scraping categoria: {category_url} (Categoria: {macro_category})")
    current_url = category_url
    page_number = 1
    total_pages = 1  # Default: 1 pagina, verrà aggiornato se troviamo l'indicatore di paginazione

    # Determina il numero totale di pagine
    try:
        driver.get(current_url)
        time.sleep(2)  
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'pagination__page-info'))
        )
        pagination_info = driver.find_element(By.CLASS_NAME, "pagination__page-info").text
        print(f"Informazioni di paginazione: {pagination_info}")
        total_pages = int(re.search(r'di (\d+)', pagination_info).group(1))
        print(f"Totale pagine per la categoria: {total_pages}")
    except Exception as e:
        print(f"Nessun indicatore di paginazione trovato per {current_url}. Assumo una sola pagina. Errore: {e}")
        total_pages = 1

    # Itera su tutte le pagine
    while page_number <= total_pages:
        retry_count = 0
        success = False

        # Costruisci l'URL della pagina corrente
        from_value = (page_number-1) * 40
        if "?" in current_url:
            base_url = current_url.split("?")[0]
            current_url = f"{base_url}?from={from_value}&size=40"
        else:
            current_url = f"{current_url}?from={from_value}&size=40"

        while retry_count < max_retries and not success:
            try:
                print(f"Caricamento pagina: {current_url} (Pagina {page_number})")
                driver.get(current_url)

                # Aspetta che i prodotti si carichino
                time.sleep(2)  
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'product-card-details__item__title'))
                )

                # Estrai i link dei prodotti
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                product_container = soup.find('div', class_='page-container')
                if product_container:
                    product_titles = product_container.find_all('div', class_='product-card-details__item__title')
                    product_items = [title.find('a') for title in product_titles if title.find('a')]
                else:
                    print(f"Contenitore 'page-container' non trovato per {current_url}, cerco direttamente i prodotti")
                    product_titles = soup.find_all('div', class_='product-card-details__item__title')
                    product_items = [title.find('a') for title in product_titles if title.find('a')]

                # Se non ci sono prodotti, potrebbe essere un errore o l'ultima pagina
                if not product_items:
                    print(f"Nessun prodotto trovato nella pagina {page_number}. Potrebbe essere un errore o l'ultima pagina effettiva.")
                    break

                for item in product_items:
                    href = item.get('href')
                    if href and '/p/' in href:
                        full_url = href if href.startswith('http') else f"https://www.decathlon.it{href}"
                        # Filtra solo i prodotti con "roller" nell'URL
                        if "roller" in full_url.lower():
                            if not any(full_url == link for link, _ in product_links_with_macro):
                                product_links_with_macro.append((full_url, macro_category))

                print(f"Pagina {page_number} - Trovati {len(product_links_with_macro)} prodotti finora.")
                success = True
                page_number += 1

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
                        print("Impossibile riavviare il driver. Passo alla prossima categoria.")
                        break
                else:
                    print(f"Massimo numero di tentativi raggiunto per {current_url}. Passo alla prossima categoria.")
                    break

        if not success:
            print(f"Fine scraping per la categoria {macro_category} a causa di errori. Passo alla prossima categoria.")
            break

    time.sleep(1)


# Funzione per estrarre i dati di un prodotto (rimane invariata)
def extract_product_data(driver, macro_category):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_data = {}

    # Estrai la sotto-categoria dal breadcrumb
    breadcrumb_items = soup.find_all('li', class_='breadcrumbs__breadcrumb-item')
    subcategory = None

    # Prendi l'ultimo elemento del breadcrumb
    if breadcrumb_items:
        subcategory = breadcrumb_items[-1].text.strip()
    
    if not subcategory:
        subcategory = "Unknown"  # Valore di default se non trovato

    # Macro-categoria e sotto-categoria
    product_data['category'] = macro_category
    product_data['subcategory'] = subcategory

    # Brand
    brand_div = soup.find('div', class_='product-info__brand')
    product_data['brand'] = brand_div.text.strip() if brand_div else None

    # Nome prodotto
    name_div = soup.find('div', class_='product-info__name')
    product_data['name'] = name_div.text.strip() if name_div else None

    # Descrizione prodotto
    description_div = soup.find('div', class_='product-info__description')
    product_data['description'] = description_div.text.strip() if description_div else None

    # Aggiungi il colore (se disponibile)
    selected_variant = soup.find('div', class_='variant-selector-headline__value')
    product_data['color'] = selected_variant.text.strip() if selected_variant else None    

    # ID prodotto
    id_div = soup.find('div', class_='product-info__product-id')
    if id_div:
        id_text = id_div.text.strip()
        id_numeric = int(re.search(r'\d+', id_text).group()) if re.search(r'\d+', id_text) else 0
        product_data['id'] = id_numeric if id_numeric else None
    else:
        product_data['id'] = None

    # Prezzo corrente
    price_div = soup.find('span', class_='price-base__current-price')
    if price_div:
        price_text = price_div.text.strip()
        price_numeric = float(re.sub(r'[^\d.,]', '', price_text).replace(',', '.'))
        product_data['price(€)'] = price_numeric if price_numeric else None
    else:
        product_data['price(€)'] = None

    # Disponibilità
    out_of_stock_div = soup.find('span', class_='price-base__out-of-stock')
    product_data['availability'] = "Not available" if out_of_stock_div else "Available"

    # Prezzo precedente
    prv_price_div = soup.find('span', class_='price-base__previous-price')
    if prv_price_div:
        prv_price_text = prv_price_div.text.strip()
        prv_price_numeric = float(re.sub(r'[^\d.,]', '', prv_price_text).replace(',', '.'))
        product_data['previous_price(€)'] = prv_price_numeric if prv_price_numeric else None
    else:
        product_data['previous_price'] = None

    # Valore sconto
    sale_div = soup.find('span', class_='price-base__commercial-message')
    if sale_div:
        sale_text = sale_div.text.strip()
        sale_numeric = float(re.search(r'\d+(?:\.\d+)?', sale_text).group()) if re.search(r'\d+(?:\.\d+)?', sale_text) else 0
        product_data['sale%'] = sale_numeric if sale_numeric else "Not on sale"
    else:
        product_data['sale%'] = "Not on sale"

    # Valutazione/5
    score_div = soup.find('span', class_='review__fullstars__score')
    if score_div:
        score_text = score_div.text.strip()
        score_numeric = float(re.search(r'\d+(?:\.\d+)?', score_text).group()) if re.search(r'\d+(?:\.\d+)?', score_text) else 0.0
        product_data['score/5'] = score_numeric if score_numeric else None
    else:
        product_data['score/5'] = None

    # Numero recensioni
    reviews_div = soup.find('div', class_='review__fullstars__votes')
    if reviews_div:
        reviews_text = reviews_div.text.strip()
        review_numeric = int(re.search(r'\d+', reviews_text).group()) if re.search(r'\d+', reviews_text) else 0
        product_data['num_reviews'] = review_numeric if review_numeric else None

    # Link prodotto
    product_data['product_link'] = driver.current_url

    # Aggiungi data e ora dell'estrazione
    product_data['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return product_data


# Step 3: Per ogni prodotto, estrai i dati e salvali in una lista
all_products = []
for product_url, macro_category in product_links_with_macro:
    print(f"Scraping prodotto: {product_url} (Categoria: {macro_category})")
    try:
        # Carica la pagina del prodotto
        driver.get(product_url)

        # Aspetta che la pagina del prodotto si carichi
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-info__name'))
        )

        # Estrai i dati del prodotto
        product_data = extract_product_data(driver, macro_category)
        if product_data:
            all_products.append(product_data)
            print(f"Elaborato: {product_data['name']}, Categoria: {product_data['category']}, Sottocategoria: {product_data['subcategory']}")
        else:
            print(f"Impossibile estrarre i dati per {product_url}")

        time.sleep(0.5)  # Ridotto a 0.5 secondi

    except Exception as e:
        print(f"Errore durante l'elaborazione del prodotto {product_url}: {e}")
        continue


# Step 4: Salva i dati in un file JSON
if all_products:
    # Crea un nome di file dinamico basato sulla data corrente
    current_date = datetime.now().strftime('%Y-%m-%d')
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    json_dir = f'decathlon_roller_products/{year}/{month}'
    json_path = f'{json_dir}/decathlon_roller_products_{current_date}.json'
    
    # Crea la directory se non esiste
    os.makedirs(json_dir, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)
    print(f"Salvati {len(all_products)} prodotti in {json_path}")
else:
    print("Nessun prodotto trovato da salvare.")

# Chiudi il driver
driver.quit()

