import time
import csv
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import visibility_of    
from scraper.scraper_utils import download_image
from config.config import RAW_IMAGES_PATH
from urllib.parse import urlparse

def scrape_hm_images():
    cService = webdriver.ChromeService(executable_path='C:\\Users\\Matthew Dang\\Desktop\\chromedriver-win64\\chromedriver.exe')
    driver = webdriver.Chrome(service=cService)

    offset = 1
    page = 1
    MAX_PAGES = 2
    metadata = []
    seen_products = set()

    existing_metadata = {}
    metadata_file = os.path.join(RAW_IMAGES_PATH, "metadata.csv")
    if os.path.exists(metadata_file):
        with open(metadata_file, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_metadata[row["title"]] = row

    while page <= MAX_PAGES:
        url = f"https://www2.hm.com/en_us/men/products/view-all.html?page={offset}"
        print(f"Scraping page {page} | URL: {url}")
        driver.get(url)
        time.sleep(3)

        products = driver.find_elements(By.CSS_SELECTOR, 'a.e759aa')
        products = products[0:1]

        for product in products:
            try:
                product_url = product.get_attribute("href")
                product_title = product.get_attribute("title")

                # Extract product ID before interacting with the element
                product_id_match = re.search(r'productpage\.(\d+)', product_url)
                if product_id_match:
                    product_id = product_id_match.group(1)[:-3]  # Remove last 3 digits
                else:
                    continue  # Skip if no product ID found

                if product_id in seen_products:
                    print(f"Skipping duplicate product ID: {product_id}")
                    continue

                seen_products.add(product_id)

                # NOW check if the element is displayed
                if not product.is_displayed():
                    continue
                
                safe_title = re.sub(r'[\\/*?:"<>|]', "", product_title).strip()[:100]
                if not safe_title:
                    continue
                product_folder = os.path.join(RAW_IMAGES_PATH, safe_title)
                os.makedirs(product_folder, exist_ok=True)

                driver.execute_script("window.open(arguments[0]);", product_url)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)


                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="next-image"]'))
                )
                color_elements = driver.find_elements(By.CSS_SELECTOR, 'div.be8654.fcc68c.a33b36.f6e252')
                color_map = {}

                price_element = driver.find_element(By.CSS_SELECTOR, 'span.edbe20.ac3d9e.d9ca8b')
                product_price = price_element.text

                fit_element = driver.find_element(By.CSS_SELECTOR, "p.d1cd7b.ca7db2.e2b79d")
                product_fit = fit_element.text.strip()

                for color in color_elements:
                    color_img = color.find_element(By.TAG_NAME, "img")
                    color_name = color_img.get_attribute("alt")
                    color_map[color_name] = color

                img_urls = []

                processed_colors = set()
                for color_name, color_element in color_map.items():
                    if color_name in processed_colors:
                        continue
                    processed_colors.add(color_name)

                    # Click the swatch to update the main gallery
                    driver.execute_script("arguments[0].click();", color_element)

                    # Scrape the updated main gallery images
                    updated_images = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="next-image"]')
                    for img in updated_images:
                        driver.execute_script("arguments[0].scrollIntoView(true);", img)
                        time.sleep(0.2)
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
                    "fit_desc": product_fit
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"Error fetching image: {e}")

        offset += 1
        page += 1

    driver.quit()

    metadata_file = os.path.join(RAW_IMAGES_PATH, "metadata.csv")
    with open(metadata_file, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "product_url", "price", "image_urls", "fit_desc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in metadata:
            writer.writerow(data)

    print(f"Scraping done. Metadata saved to {metadata_file}")