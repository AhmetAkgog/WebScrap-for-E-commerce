import sys
import re
import json
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

class ScraperThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, username, password, base_urls, supplier_id, access_token):
        super().__init__()
        self.username = username
        self.password = password
        self.base_urls = base_urls
        self.supplier_id = supplier_id
        self.access_token = access_token

    def run(self):
        # Execute scraping process
        self.scrape()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        service = Service('WEBDRIVER PATH')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def login(self, driver, username, password):
        login_url = "https://www.yeninesiltoptanci.com/UyeGiris"
        driver.get(login_url)
        driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(username)
        driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(password)
        driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click()
        time.sleep(5)
        return "SOME STRING VALUE APPEARS WHEN ONLY LOGGED IN" in driver.page_source

    def get_cookies(self, driver):
        cookies = driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def get_product_urls(self, driver, url):
        driver.get(url)
        for _ in range(10):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_links = [a for a in soup.find_all('a') if 'detailUrl' in a.get('class', []) and len(a.get('class', [])) == 1]
        return [urljoin(url, link.get('href')) for link in product_links]

    def get_page_html(self, url, cookies=None, timeout=40):
        try:
            session = requests.Session()
            if cookies:
                session.cookies.update(cookies)
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.log_signal.emit(f"An error occurred: {e}")
            return None

    def scrape_product_pages(self, product_urls, cookies, delay=2):
        all_html = []
        for url in product_urls:
            html = self.get_page_html(url, cookies=cookies)
            if html:
                all_html.append(html)
                self.log_signal.emit(f"Successfully retrieved {url}")
            else:
                self.log_signal.emit(f"Failed to retrieve {url}")
            time.sleep(delay)
        return all_html

    def extract_product_data(self, html, start_barcode, previous_product_name=None, color_suffix=1):
        soup = BeautifulSoup(html, 'html.parser')

        # Use regex to find the JavaScript variable containing productDetailModel
        match = re.search(r'var productDetailModel = ({.*?});', html, re.DOTALL)
        if not match:
            print("Could not find the productDetailModel variable in the HTML.")
            return [], start_barcode, previous_product_name, color_suffix

        # Parse the JSON data
        product_detail_model = json.loads(match.group(1))

        # Extract the productName
        product_name = product_detail_model.get('productName', '')

        if 'YNT' in product_name:
            product_name = product_name.replace('YNT', 'Velours Violet')

        if product_name != previous_product_name:
            color_suffix += 1
            previous_product_name = product_name

        description_div = soup.find('div', {'id': 'divTabOzellikler'})
        product_description = description_div.get_text(separator=' ', strip=True) if description_div else 'No description available'

        img_divs = soup.find_all('div', {'class': 'AltImgCapSmallImg'})
        image_urls = []
        max_images = 8

        for img_div in img_divs:
            if len(image_urls) >= max_images:
                break  # Stop processing if we have already collected 8 image URLs
            img_tag = img_div.find('img')
            if img_tag:
                data_cloudzoom = img_tag.get('data-cloudzoom')
                if data_cloudzoom:
                    cloudzoom_data = json.loads(data_cloudzoom.replace("'", '"'))
                    image_url = cloudzoom_data.get('image')
                    if image_url:
                        image_urls.append({"url": image_url})

        products = product_detail_model.get('products', [])
        extracted_data = []
        productMainId = "MODELKODU"
        brandID = 1860622
        categoryId = 574
        profitMargin = 0.3
        shippingFee = 61.9
        commissionRate = 0.215

        size_mapping = {
            'S/M': '7117',
            'L/XL': '7112',
            '2XL/3XL': '5370',
            '2XL-3XL': '5370',
            'XS' : '6964',
            'S' : '3961',
            'M' : '3960',
            'L' : '3959',
            'XL' : '3962',
            '2XL' : '5367',
            '3XL' : '5764',
            '4XL' : '6104',
            '5XL' : '6287',
            'Standart' : '144271',
            'STANDART' : '144271'
        }

        category_attribute_mapping = {
            574: [47,338,346,343,200],  #String
            1182: [48],  #Elbise
            # Add more mappings as needed
        }

        attribute_ids = category_attribute_mapping.get(categoryId, [])

        for product in products:
            tedarikci_kodu_values = product.get('tedarikciKodu', '').split('|')
            color = tedarikci_kodu_values[2] if len(tedarikci_kodu_values) > 2 else None
            size = tedarikci_kodu_values[3] if len(tedarikci_kodu_values) > 3 else None
            print(product.get('urunFiyatiOrjinal'))
            print(type(float(product.get('urunFiyatiOrjinal'))))
            if color:
                color = f"{color}{color_suffix}"

            size_code = size_mapping.get(size, size)

            attributes = []

            if 47 in attribute_ids:
                attributes.append({
                    "attributeId": 47,
                    "customAttributeValue": color
                })

            # Add size attribute if it exists
            if 338 in attribute_ids:
                attributes.append({
                    "attributeId": 338,
                    "attributeValueId": size_code
                })

            # Add additional attributes based on categoryId
            if 346 in attribute_ids:
                attributes.append({
                    "attributeId": 346,
                    "attributeValueId": 4293
                })

            if 343 in attribute_ids:
                attributes.append({
                    "attributeId": 343,
                    "attributeValueId": 4295
                })

            if 200 in attribute_ids:
                attributes.append({
                    "attributeId": 200,
                    "attributeValueId": 22131
                })

            if 48 in attribute_ids:
                attributes.append({
                    "attributeId": 48,
                    "attributeValueId": 1200547
                })


            data = {
                'barcode': start_barcode,
                'title': product_name,
                'productMainId': productMainId,
                'brandId': brandID,
                'categoryId': categoryId,
                'quantity': product.get('stokAdedi'),
                'stockCode': product.get('stokKodu'),
                'dimensionalWeight': 0,
                'description': product_description,
                'currencyType': 'TRY',
                'listPrice': (product.get('urunFiyatiOrjinal')+ product.get('urunFiyatiOrjinalKDV') + shippingFee)*(1+profitMargin)/(1-commissionRate),
                'salePrice': (product.get('urunFiyatiOrjinal')+ product.get('urunFiyatiOrjinalKDV') + shippingFee)*(1+profitMargin)/(1-commissionRate),
                'vatRate': 10,
                'cargoCompanyId': 7870233582,
                'images': image_urls,
                'attributes': attributes
            }
            extracted_data.append(data)

            start_barcode += 1
        return extracted_data, start_barcode, previous_product_name, color_suffix

    def send_product_data_to_trendyol(self, batched_data):
        url = f"https://api.trendyol.com/sapigw/suppliers/{self.supplier_id}/v2/products"
    
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "200300444 - Trendyolsoft",
            "Content-Type": "application/json"
        }
    
        response = requests.post(url, headers=headers, json=batched_data)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                batch_request_id = response_data.get("batchRequestId", "No batch request ID found")
                self.log_signal.emit(f"Batch Request ID: {batch_request_id}")
            except json.JSONDecodeError:
                self.log_signal.emit("Failed to parse JSON response.")
        else:
            self.log_signal.emit(f"Failed to send product data. Status code: {response.status_code}")
            try:
                error_details = response.json()
                self.log_signal.emit(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                self.log_signal.emit(f"Response: {response.text}")
    
    def save_data(self, all_product_data):
        formatted_data = {"items": all_product_data}
        json_output = json.dumps(formatted_data, indent=2, ensure_ascii=False)
        with open("product_data.json", "w", encoding="utf-8") as f:
            f.write(json_output)

    def scrape(self):
        driver = self.setup_driver()
        if not self.login(driver, self.username, self.password):
            self.log_signal.emit("Login failed!")
            driver.quit()
            return

        cookies = self.get_cookies(driver)
        all_product_data = []
        start_barcode = 645222333
        previous_product_name = None
        color_suffix = 1

        for base_url in self.base_urls:
            self.log_signal.emit(f"Scraping URL: {base_url}")
            product_urls = self.get_product_urls(driver, base_url.strip())
            if not product_urls:
                self.log_signal.emit(f"No product URLs found for {base_url}.")
                continue

            all_html = self.scrape_product_pages(product_urls, cookies)
            for html in all_html:
                product_data, start_barcode, previous_product_name, color_suffix = self.extract_product_data(
                    html, start_barcode, previous_product_name, color_suffix
                )
                all_product_data.extend(product_data)

        driver.quit()

        # Batch sending the data to Trendyol
        batch_size = 1  # Number of products per batch, adjust as needed

        for i in range(0, len(all_product_data), batch_size):
            batch = all_product_data[i:i + batch_size]
            batched_data = {"items": batch}

            self.send_product_data_to_trendyol(batched_data)

            self.log_signal.emit(f"Batch {i // batch_size + 1} sent to Trendyol.")

            time.sleep(3)  # Sleep to avoid hitting API rate limits

        # Save all product data to a JSON file after sending
        self.save_data(all_product_data)
        self.log_signal.emit("Scraping completed, data sent to Trendyol, and saved to 'product_data.json'.")

class ScraperGUI(QMainWindow):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Web Scraper GUI")
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout()

        # Display the username (optional)
        login_info_layout = QHBoxLayout()
        login_info_layout.addWidget(QLabel(f"Logged in as: {self.username}"))
        main_layout.addLayout(login_info_layout)

        supplier_layout = QHBoxLayout()
        supplier_layout.addWidget(QLabel("Supplier ID:"))
        self.supplier_id = QLineEdit()
        supplier_layout.addWidget(self.supplier_id)

        supplier_layout.addWidget(QLabel("Token:"))
        self.access_token = QLineEdit()
        supplier_layout.addWidget(self.access_token)

        main_layout.addLayout(supplier_layout)

        urls_layout = QHBoxLayout()
        urls_layout.addWidget(QLabel("Base URLs (comma-separated):"))
        self.urls_input = QLineEdit()
        urls_layout.addWidget(self.urls_input)
        main_layout.addLayout(urls_layout)

        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        main_layout.addWidget(self.start_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def log(self, message):
        self.log_output.append(message)

    def start_scraping(self):
        supplier_id = self.supplier_id.text()
        access_token = self.access_token.text()
        base_urls = self.urls_input.text().split(',')

        if not base_urls or not supplier_id or not access_token:
            QMessageBox.warning(self, "Input Error", "Please provide all required inputs.")
            return

        self.thread = ScraperThread(self.username, self.password, base_urls, supplier_id, access_token)
        self.thread.log_signal.connect(self.log)
        self.thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperGUI("default_user", "default_password")  # Placeholder for testing
    window.show()
    sys.exit(app.exec_())
