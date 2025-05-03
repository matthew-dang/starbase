import time
import csv
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import visibility_of    
from scraper.scraper_utils import download_image
from config.config import RAW_IMAGES_PATH3
from urllib.parse import urlparse

chrome_options = Options()
chrome_options.add_argument("--log-level=3")

def load_metadata():
    metadata_file = os.path.join(RAW_IMAGES_PATH3, "metadata.csv")
    visited_urls = set()
    with open(metadata_file, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'product_url' in row:
                parsed = urlparse(row['product_url'])
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                visited_urls.add(base_url)    

    return visited_urls

def scrape_abercrombie():
    cService = Service(executable_path='C:\\Users\\Matthew Dang\\Desktop\\chromedriver-win64\\chromedriver.exe')
    driver = webdriver.Chrome(service=cService, options=chrome_options)

    offset = 0
    page = 1
    MAX_PAGES = 3
    metadata = []
    seen_products = set()

    while page <= MAX_PAGES:
        url = f"https://www.abercrombie.com/shop/us/mens-new-arrivals?rows=90&sort=bestmatch&start={offset}"
        print(f"Scraping page {page} | URL: {url}")
        driver.get(url)
        scroll_partway(driver, num_scrolls=1, pause_time=2)
        time.sleep(1)

        products = driver.find_elements(By.CSS_SELECTOR, 'div.catalog-productCard-module__hasHoverImage')
        visited_urls = load_metadata()
        time.sleep(10)

        for product in products:
            try:
                product_url_tag = product.find_element(By.TAG_NAME, "a")
                full_url = product_url_tag.get_attribute("href")
                parsed_url = urlparse(full_url)
                product_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                product_title_tag = product_url_tag.find_element(By.CSS_SELECTOR, 'img[data-aui="product-card-image"]')
                product_title_seen = product_title_tag.get_attribute("alt").split(', ')
                product_title_seen = product_title_seen[0]
                if product_title_seen in seen_products:
                    continue
                seen_products.add(product_title_seen) 

                if product_url in visited_urls:
                    continue
                visited_urls.add(product_url)

                driver.execute_script("window.open(arguments[0]);", full_url)
                driver.switch_to.window(driver.window_handles[-1])

                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.product-page-gallery-mfe-container'))
                    )
                except:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                scroll_partway(driver, num_scrolls=1, pause_time=2)

                product_details = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="desktop-name-price-reviews"]')
                product_title = product_details.find_element(By.TAG_NAME, 'h1').text
                product_price_tag = product_details.find_element(By.CSS_SELECTOR, 'div.product-price-container')
                product_price = product_price_tag.find_element(By.CSS_SELECTOR, 'span.screen-reader-text').text

                safe_title = re.sub(r'[\\/*?:"<>|]', "", product_title).strip()[:100]
                if not safe_title:
                    continue
                product_folder = os.path.join(RAW_IMAGES_PATH3, safe_title)
                os.makedirs(product_folder, exist_ok=True)

                main_product = driver.find_element(By.CSS_SELECTOR, 'section.mfe-product-page__info-container')
                color_elements = main_product.find_elements(By.CSS_SELECTOR, 'input[name="swatch"]')

                color_map = {}

                for color in color_elements:
                    wrapper = color.find_element(By.XPATH, "./ancestor::div[contains(@class, 'swtg-input-inner-wrapper')]")
                    
                    try:
                        color_img = wrapper.find_element(By.TAG_NAME, "img")
                        color_name = color_img.get_attribute("alt").title()
                        color_map[color_name] = color
                    except:
                        print("No img found for swatch")

                img_urls = []
                processed_colors = set()
                for color_name, color_element in color_map.items():
                    # Skip duplicates if needed
                    if color_name in processed_colors:
                        continue
                    processed_colors.add(color_name)

                    # Click the swatch to update the main gallery
                    driver.execute_script("arguments[0].click();", color_element)
                    time.sleep(1.5)

                    # Scrape the updated main gallery images
                    updated_images = driver.find_elements(By.CSS_SELECTOR, 'div.product-page-gallery-mfe-container')
                    for img in updated_images:
                        if img.is_displayed():
                            image_tag = img.find_element(By.TAG_NAME, "img")
                            src = image_tag.get_attribute("src")

                            if not src or src.startswith("data:"):
                                continue
                            # Prepare color folder
                            safe_color_name = re.sub(r'[\\/*?:"<>|/]', "_", color_name)
                            color_folder = os.path.join(product_folder, safe_color_name)
                            os.makedirs(color_folder, exist_ok=True)

                            # Download and track the image
                            download_image(src, color_folder, min_width=200, min_height=200)
                            img_urls.append(src)
                            print(f"Downloaded {src} to {color_folder}")

                metadata.append({
                    "title": product_title,
                    "product_url": product_url,
                    "price": product_price,
                    "image_urls": img_urls,
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"Error fetching image: {e}")

        offset += 90
        page += 1

    driver.quit()

    metadata_file = os.path.join(RAW_IMAGES_PATH3, "metadata.csv")
    with open(metadata_file, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "product_url", "price", "image_urls"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in metadata:
            writer.writerow(data)

    print(f"Scraping done. Metadata saved to {metadata_file}")


def scroll_partway(driver, num_scrolls=2, pause_time=0.5):
    for _ in range(num_scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(pause_time)