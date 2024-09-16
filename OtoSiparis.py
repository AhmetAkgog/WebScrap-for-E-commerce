import requests
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

class SiparisBilgisi(QWidget):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.driver = None  # Initialize WebDriver to be used later

        # Set up the user interface
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Supplier ID input
        self.supplier_id_label = QLabel("Supplier ID:")
        self.supplier_id_input = QLineEdit()
        layout.addWidget(self.supplier_id_label)
        layout.addWidget(self.supplier_id_input)

        # Token input
        self.token_label = QLabel("Token:")
        self.token_input = QLineEdit()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_input)

        # Submit button
        self.submit_button = QPushButton("Fetch Orders")
        self.submit_button.clicked.connect(self.fetch_orders)
        layout.addWidget(self.submit_button)

        # Text area to display results
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        # Set the layout
        self.setLayout(layout)

    def fetch_orders(self):
        supplier_id = self.supplier_id_input.text()
        token = self.token_input.text()

        if not supplier_id or not token:
            self.show_message("Error", "Both Supplier ID and Token are required!")
            return

        # Prepare the URL and headers
        url = f"https://api.trendyol.com/sapigw/suppliers/{supplier_id}/orders?status=Created"
        headers = {
            "Authorization": f"Basic {token}",
            "User-Agent": "200300444 - Trendyolsoft"
        }

        # Send the GET request
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()

                # Display data in the text area
                self.results_text.setText(json.dumps(data, ensure_ascii=False, indent=4))

                # Write data to a JSON file
                with open('orders_data.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

                self.show_message("Success", "Orders data retrieved and saved successfully.")

                # Extract merchantSku and login to the website
                self.extract_merchant_sku_and_login(data)
            else:
                self.show_message("Error", f"Failed to retrieve data. Status code: {response.status_code}")
        except Exception as e:
            self.show_message("Error", f"An error occurred: {str(e)}")

    def extract_merchant_sku_and_login(self, data):
        try:
            # Extract the first merchantSku from the 'lines' in the orders data
            orders = data.get("content", [])
            if not orders:
                self.show_message("Error", "No orders found in the response.")
                return

            # Assuming we only take the first order and the first line
            first_order = orders[0]
            lines = first_order.get("lines", [])
            if not lines:
                self.show_message("Error", "No lines found in the first order.")
                return

            merchant_sku = lines[0].get("merchantSku", None)
            if merchant_sku:
                self.show_message("Success", f"Extracted merchantSku: {merchant_sku}")
                # Proceed to login and enter merchantSku
                self.login_to_website(merchant_sku)
            else:
                self.show_message("Error", "merchantSku not found in the lines.")
        except Exception as e:
            self.show_message("Error", f"An error occurred while extracting merchantSku: {str(e)}")

    def login_to_website(self, merchant_sku):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # WONT WORK WITHOUT FULLSCREEN I DONT KNOW WHY I LOST 1 DAY TO THIS
        service = Service('YOUR WEBDRIVER PATH HERE')  # Update with your chromedriver path
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Navigate to the login page
            self.driver.get("https://www.yeninesiltoptanci.com/UyeGiris")

            # Find and fill the username and password fields
            self.driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(self.username)
            self.driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(self.password)
            self.driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click()

            # Optional: Wait for a few seconds to ensure login completes
            time.sleep(5)

            if self.driver.current_url == "https://www.yeninesiltoptanci.com/":
                self.show_message("Success", "Logged in successfully.")

                # Enter merchantSku into the input field after login
                self.enter_merchant_sku(merchant_sku)
            else:
                self.show_message("Error", "Failed to login.")
        except Exception as e:
            self.show_message("Error", f"An error occurred during login: {str(e)}")
        finally:
            # Cleanup: don't quit the driver if you want to reuse it later
            pass

    def enter_merchant_sku(self, merchant_sku):
        try:
            # Wait until the input field is visible
            merchant_sku_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "txtbxArama"))
            )
            # Enter the merchant SKU
            merchant_sku_input.send_keys(merchant_sku)
    
            # Wait for the search button to be clickable and click it
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnKelimeAra"))
            )
            search_button.click()
    
            # Optional: After clicking the button, you can print the current URL
            current_url = self.driver.current_url
            self.show_message("Current URL", current_url)


        except Exception as e:
            self.show_message("Error", f"An error occurred while entering merchantSku: {str(e)}")

    def manage_cookies(self):
        if self.driver:
            cookies = self.get_cookies()
            # Do something with cookies here, e.g., save to file or use them for further requests
            print("Cookies:", cookies)

    def get_cookies(self):
        if self.driver:
            cookies = self.driver.get_cookies()
            return {cookie['name']: cookie['value'] for cookie in cookies}
        return {}

    def show_message(self, title, message):
        print(f"{title}: {message}")

    def closeEvent(self, event):
        # Ensure the WebDriver is closed when the widget is closed
        if self.driver:
            self.driver.quit()
        event.accept()