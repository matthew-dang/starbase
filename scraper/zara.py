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
from config.config import RAW_IMAGES_PATH2
from urllib.parse import urlparse

def load_metadata():
    metadata_file = os.path.join(RAW_IMAGES_PATH2, "metadata.csv")
    visited_urls = set()
    with open(metadata_file, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            visited_urls.add(row.get('product_url'))
    return visited_urls

def scrape_zara():
    cService = webdriver.ChromeService(executable_path='C:\\Users\\Matthew Dang\\Desktop\\chromedriver-win64\\chromedriver.exe')
    driver = webdriver.Chrome(service=cService)

    metadata = []

    url = f"https://www.zara.com/us/en/man-all-products-l7465.html?v1=2443335&regionGroupId=8"
    print(f"Scraping page")
    driver.get(url)
    scroll_partway(driver, num_scrolls=50)

    products = driver.find_elements(By.CSS_SELECTOR, 'a.product-link.product-grid-product__link.link')
    visited_urls = load_metadata()

    for product in products:
        try:
            product_url = product.get_attribute("href")

            if product_url in visited_urls:
                continue
            visited_urls.add(product_url)

            driver.execute_script("window.open(arguments[0]);", product_url)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(1)
            scroll_partway(driver, num_scrolls=2, pause_time=2)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'img.media-image__image.media__wrapper--media'))
            )
            color_element = driver.find_element(By.CSS_SELECTOR, 'div.product-detail-view__main-info')


            product_title_tag = color_element.find_element(By.CSS_SELECTOR, 'h1.product-detail-info__header-name')
            product_title = product_title_tag.text
            product_title = product_title[0].upper() + product_title[1:].lower()
            product_title = product_title.title()

            product_price_tag = color_element.find_element(By.CSS_SELECTOR, 'span.money-amount__main')
            product_price = product_price_tag.text.replace(" ", "")
            
            safe_title = re.sub(r'[\\/*?:"<>|]', "", product_title).strip()[:100]
            if not safe_title:
                continue
            product_folder = os.path.join(RAW_IMAGES_PATH2, safe_title)
            os.makedirs(product_folder, exist_ok=True)

            img_urls = []
            color_map = {}
            color_elements = driver.find_elements(By.CSS_SELECTOR, 'button[data-qa-action="select-color"]')

            if not color_elements:
                color_name_raw = color_element.find_element(By.CSS_SELECTOR, 'p[data-qa-qualifier="product-detail-info-color"]').text.strip()
                color_name = color_name_raw.split('|')[0].strip()
                safe_color_name = re.sub(r'[\\/*?:"<>|/]', "_", color_name)
                safe_color_name = safe_color_name.title()
                
                final_folder = os.path.join(product_folder, safe_color_name)

                os.makedirs(final_folder, exist_ok=True)
                gallery_images = driver.find_elements(By.CSS_SELECTOR, 'img.media-image__image.media__wrapper--media')
                
                
                for img_tag in gallery_images:
                    src = img_tag.get_attribute("src")
                    if src and not src.startswith("data:"):
                        download_image(src, final_folder, min_width=200, min_height=200)
                        img_urls.append(src)
                        print(f"Downloaded {src} to {final_folder}")

            for color in color_elements:
                outer_html = color.get_attribute('outerHTML')

                match = re.search(r'<span class="screen-reader-text">(.*?)</span>', outer_html)
                if match:
                    color_name = match.group(1).strip()
                color_map[color_name] = color

            processed_colors = set()

            for color_name, color_element in color_map.items():
                driver.execute_script("window.scrollTo(0, 0);")
                if color_name in processed_colors:
                    continue
                processed_colors.add(color_name)

                driver.execute_script("arguments[0].click();", color_element)
                gallery_images = driver.find_elements(By.CSS_SELECTOR, 'picture[data-qa-qualifier="media-image"]')

                time.sleep(1)
                scroll_partway(driver, num_scrolls=2, pause_time=2)

                for img_tag in gallery_images:
                    src_tag = img_tag.find_element(By.TAG_NAME, "img")
                    src = src_tag.get_attribute("src")

                    if src and not src.startswith("data:"):
                        safe_color_name = re.sub(r'[\\/*?:"<>|/]', "_", color_name)
                        color_folder = os.path.join(product_folder, safe_color_name)
                        os.makedirs(color_folder, exist_ok=True)

                        download_image(src, color_folder, min_width=200, min_height=200)
                        img_urls.append(src)
                        print(f"Downloaded {src} to {color_folder}")

            metadata.append({
                "title": product_title,
                "product_url": product_url,
                "price": product_price,
                "image_urls": img_urls
            })

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"Error fetching image: {e}")


    driver.quit()

    metadata_file = os.path.join(RAW_IMAGES_PATH2, "metadata.csv")

    file_exists = os.path.isfile(metadata_file)

    with open(metadata_file, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "product_url", "price", "image_urls"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for data in metadata:
            writer.writerow(data)

    print(f"Scraping done. Metadata saved to {metadata_file}")


def scroll_partway(driver, num_scrolls=2, pause_time=0.5):
    for _ in range(num_scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(pause_time)

def scroll_to_fraction(driver, fraction=0.5, pause_time=2):
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_height = total_height * fraction
    driver.execute_script(f"window.scrollTo(0, {scroll_height});")
    time.sleep(pause_time)