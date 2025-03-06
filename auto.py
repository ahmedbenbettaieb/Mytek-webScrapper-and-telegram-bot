from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from queries import INSERT_QUERY, CREATE_TABLE_QUERY
from dbConnection import get_db_connection


class ChromeDriverManager:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.cursor.execute(CREATE_TABLE_QUERY)
        self.conn.commit()

    def init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(
            service=Service(self.driver_path), options=chrome_options
        )
        return self.driver

    def navigate_to_url(self, url):
        if self.driver:
            self.driver.get(url)
        else:
            raise Exception("Driver is not initialized. Call init_driver() first.")

    def extract_product_data(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.select("#maincontent .products .product-item-info")
        return products

    def extract_raw_price(self, product):
        price_element = product.select_one('[data-price-type="finalPrice"]')
        if price_element:
            price_amount = price_element.get("data-price-amount")
            if price_amount:
                return float(price_amount)
        return None

    def transform_product_data(self, product):
        try:
            name = product.select_one(".product-item-name a").text.strip()
            sku = product.select_one(".skuDesktop").text.strip()
            description = product.select_one(".product-item-description p").text.strip()
            price = self.extract_raw_price(product)
            availability = product.select_one(".stock")
            availability_status = (
                "Out of Stock"
                if availability and "Epuisé" in availability.text
                else "In Stock"
            )
            return {
                "name": name,
                "sku": sku,
                "description": description,
                "price": price,
                "availability": availability_status,
            }
        except AttributeError:
            return None

    def load_product_data_to_db(self, products_data):
        for product in products_data:
            if product:
                self.cursor.execute(
                    INSERT_QUERY,
                    (
                        product["price"],
                        product["sku"],
                        product["name"],
                        product["description"],
                        product["availability"],
                    ),
                )
        self.conn.commit()

    def run_etl_process(self, url):
        products = self.extract_product_data(url)
        transformed_data = [
            self.transform_product_data(product) for product in products
        ]
        self.load_product_data_to_db(transformed_data)

    def get_max_page(self):
        if self.driver:
            try:
                last_page_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//li[@class='item']/a[@class='page last']")
                    )
                )
                max_page = last_page_element.find_element(By.XPATH, "./span[2]").text
                return int(max_page)
            except Exception as e:
                print(f"Error finding max page: {e}")
                return None
        else:
            raise Exception("Driver is not initialized. Call init_driver() first.")

    def go_to_next_page(self):
        if self.driver:
            try:
                max_pages = self.get_max_page()
                if max_pages:
                    for i in range(1, max_pages + 1):
                        if i > 1:
                            next_page_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable(
                                    (
                                        By.XPATH,
                                        f"//li[@class='item']/a[@class='page']/span[text()='{i}']",
                                    )
                                )
                            )
                            next_page_button.click()
                        current_url = self.driver.current_url
                        self.run_etl_process(current_url)
            except Exception as e:
                print(f"Error navigating pages: {e}")
        else:
            raise Exception("Driver is not initialized. Call init_driver() first.")

    def close_driver(self):
        if self.driver:
            self.driver.quit()
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    driver_path = r"C:\Program Files\chromedriver-win64\chromedriver.exe"
    chrome_driver = ChromeDriverManager(driver_path)

    try:
        chrome_driver.init_driver()
        chrome_driver.navigate_to_url(
            "https://www.mytek.tn/informatique/ordinateurs-portables/pc-portable.html"
        )
        chrome_driver.go_to_next_page()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chrome_driver.close_driver()

    print("ETL process completed successfully.")