import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.handm import scrape_hm_images
from scraper.zara import scrape_zara
from scraper.abercrombie import scrape_abercrombie

def main():
    scrape_abercrombie()

if __name__ == "__main__":
    main()