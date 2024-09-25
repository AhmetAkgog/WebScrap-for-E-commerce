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
            # Extract all orders
            orders = data.get("content", [])
            if not orders:
                self.show_message("Error", "No orders found in the response.")
                return

            # Initialize WebDriver once
            self.initialize_driver()

            # Loop through each order
            for order in orders:
                order_id = order.get('id')
                lines = order.get("lines", [])
                if not lines:
                    self.show_message("Error", f"No lines found in order ID: {order_id}")
                    continue  # Go to the next order if no lines are found

                skip_order = False  # A flag to skip the rest of the order
                for index, line in enumerate(lines):
                    merchant_sku = line.get("merchantSku", None)
                    product_size = line.get("productSize", None)
                    quantity = line.get("quantity", 1)  # Extract quantity

                    if merchant_sku and product_size and quantity is not None:
                        self.show_message("Success", f"Extracted merchantSku: {merchant_sku}, Product Size: {product_size}, Quantity: {quantity}")

                        # Determine if this is the last product in the order
                        is_last_product = index == len(lines) - 1

                        # Use the same tab for each product search
                        size_matched = self.enter_merchant_sku(merchant_sku, product_size, quantity, is_last_product, order,order_id)

                        if not size_matched:
                            skip_order = True  # If size was out of stock, skip the rest of the products in this order
                            break
                    else:
                        self.show_message("Error", "merchantSku, productSize, or quantity not found in the lines.")

                if skip_order:
                    self.show_message("Info", f"Skipping order ID: {order_id} due to out of stock sizes.")
                    continue

        except Exception as e:
            self.show_message("Error", f"An error occurred while extracting merchantSku, productSize, and quantity: {str(e)}")


    def initialize_driver(self):
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            service = Service('C:/Users/ahmet/Desktop/Yazılım/chromedriver-win64/chromedriver.exe')  # Update with your chromedriver path
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            try:
                # Navigate to the login page and login once
                self.driver.get("https://www.yeninesiltoptanci.com/UyeGiris")
                self.driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(self.username)
                self.driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(self.password)
                self.driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click()

                # Wait for login to complete
                time.sleep(5)

                if self.driver.current_url == "https://www.yeninesiltoptanci.com/":
                    self.show_message("Success", "Logged in successfully.")
                else:
                    self.show_message("Error", "Failed to login.")
            except Exception as e:
                self.show_message("Error", f"An error occurred during login: {str(e)}")

    def update_package_status(self, order_id, line_id, quantity):
        supplier_id = self.supplier_id_input.text()
        token = self.token_input.text()
        url = f"https://api.trendyol.com/sapigw/suppliers/{supplier_id}/shipment-packages/{order_id}"
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }

        data = {
            "lines": [
                {
                    "lineId": line_id,  # Pass the lineId dynamically
                    "quantity": quantity  # Pass the quantity dynamically
                }
            ],
            "params": {},
            "status": "Picking"
        }

        try:
            # Send the PUT request to update the package status
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                print("Package status updated successfully.")
            else:
                print(f"Failed to update package status. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"An error occurred while updating package status: {str(e)}")

    def enter_merchant_sku(self, merchant_sku, product_size, quantity, is_last_product, order, order_id):
        try:
            # Wait until the input field is visible
            merchant_sku_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "txtbxArama"))
            )
            # Clear any previous input and enter the new merchant SKU
            merchant_sku_input.clear()
            merchant_sku_input.send_keys(merchant_sku)

            # Wait for the search button to be clickable and click it
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnKelimeAra"))
            )
            search_button.click()

            self.show_message("Current URL", self.driver.current_url)

            # Wait until the search results are loaded and the product link is clickable
            product_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "productName.detailUrl"))
            )
            product_link.click()

            self.show_message("Success", "Clicked on the product link.")

            # Wait for the size options to load
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "size_box"))
            )

            # Find all available size options
            size_boxes = self.driver.find_elements(By.CLASS_NAME, "size_box")

            # Loop through the size boxes to find the one that matches the product_size and is in stock
            matched = False
            for size_box in size_boxes:
                size_text = size_box.text.strip()
                stock = size_box.get_attribute("data-stock")  # Check the stock value
                is_nostok = "nostok" in size_box.get_attribute("class")  # Check if it is out of stock

                if product_size in size_text:
                    if is_nostok or stock == "0":
                        self.show_message("Info", f"Size '{product_size}' is out of stock.")
                        self.handle_out_of_stock()  # Handle out-of-stock scenario
                        matched = False
                        return False  # Return False to indicate out-of-stock, move to the next order
                    else:
                        # Click on the size if it matches and is in stock
                        size_box.click()
                        self.show_message("Success", f"Selected size '{product_size}' with stock: {stock}.")
                        matched = True
                        break

            if not matched:
                self.show_message("Error", f"Size '{product_size}' not found or not available.")
                return matched

            # Now, after clicking the size box, check the product code (merchantSku) match
            product_code_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "divUrunKodu"))
            )

            # Extract the text from the product code element, removing "mpn:" prefix if present
            product_code = product_code_element.get_attribute("content").replace("mpn:", "")

            # Check if the product code (merchantSku) matches
            if merchant_sku not in product_code:
                self.show_message("Error", f"Merchant SKU '{merchant_sku}' does not match the product code '{product_code}'!")
                self.handle_out_of_stock()
                return False  # Move to the next order

            self.show_message("Success", f"Merchant SKU '{merchant_sku}' matches the product code '{product_code}'.")

            # Wait for the "Sepete Ekle" (Add to Basket) button to be clickable and click it
            add_to_basket_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "Addtobasket"))
            )
            add_to_basket_button.click()
            self.show_message("Success", "Clicked on 'Sepete Ekle' to add the item to the basket.")

            # After adding to basket, handle the quantity if greater than 1
            if quantity > 1:
                self.increment_quantity(quantity - 1)

            # After handling the quantity, decide whether to finish the order or continue shopping
            if is_last_product:
                # If it's the last product in the order, click the 'Complete Order' button
                complete_order_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "modalSepetimBtn"))
                )
                time.sleep(3)
                complete_order_button.click()  # Complete the order
    
                self.show_message("Success", "Clicked on 'Complete Order' to finish the order.")
    
                # Get cargoTrackingNumber and enter it into the textarea
                cargo_tracking_number = order.get("cargoTrackingNumber", "")
                self.enter_cargo_tracking_number(cargo_tracking_number)
    
                # After entering the cargo tracking number, click the "SİPARİŞ TAMAMLA" button
                siparis_tamamla_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "lnkBtnSiparisKaydet2"))
                )
                siparis_tamamla_button.click()
            
                self.show_message("Success", "Clicked on 'SİPARİŞ TAMAMLA' to complete the order.")

                bakiye_kullan_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnBakiyeKullan"))
                )
                bakiye_kullan_button.click()
            
                self.show_message("Success", "Clicked on 'BAKİYE KULLAN' to complete the order.")

                time.sleep(3)

                evet_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
                )
                evet_button.click()
            
                self.show_message("Success", "Clicked on 'Evet' to complete the order.")

                line_id = 0  # Set this to the appropriate line ID as needed
                quantity = 1  # Set this to the appropriate quantity as needed
                self.update_package_status(order_id, line_id, quantity)
                
            else:
                # Otherwise, click the 'Continue Shopping' button
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "modalDevamEtBTn"))
                )
                continue_button.click()  # Continue shopping
                self.show_message("Info", "Clicked on 'Continue Shopping'.")
    
            return True  # Indicate success
    
        except Exception as e:
            self.show_message("Error", f"An error occurred: {str(e)}")
            return False  # If there's an error, move to the next order

    def increment_quantity(self, times):
        try:
            # Wait until the increment button is visible
            increment_button = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "urunDetayAdetArttirma"))
            )

            # Click the increment button `times` times
            for _ in range(times):
                increment_button.click()
                time.sleep(1)  # Optionally wait between clicks for stability

            self.show_message("Success", f"Incremented quantity by {times}.")
        except Exception as e:
            self.show_message("Error", f"An error occurred while incrementing quantity: {str(e)}")
        
    def handle_out_of_stock(self):
        try:
            # Click on the cart title to open the cart
            cart_title = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "header-cart-title"))
            )
            cart_title.click()
    
            self.show_message("Info", "Opened the cart.")
    
            # Wait until the cart items are visible
            time.sleep(2)  # Give some time for the cart to open
    
            # Find all remove links in the cart
            remove_links = self.driver.find_elements(By.XPATH, "//a[contains(@onclick, 'window.cart.remove.executeClient')]")
    
            # Click each remove link
            for link in remove_links:
                self.driver.execute_script("arguments[0].click();", link)
                self.show_message("Info", "Clicked on a remove link.")
    
            self.show_message("Success", "Removed all items from the cart.")
    
            # Wait for 5 seconds before closing the cart modal
            time.sleep(5)
    
            # Click on the close button to close the cart modal
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "modal-close"))
            )
            close_button.click()
    
            self.show_message("Success", "Clicked on the close button to close the cart.")
    
        except Exception as e:
            self.show_message("Error", f"An error occurred while handling out-of-stock items: {str(e)}")

    def enter_cargo_tracking_number(self, cargo_tracking_number):
        try:
            # Wait until the textarea is visible
            textarea = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "mainHolder_txtbxSiparisNotu"))
            )
            # Clear any previous input and enter the new cargo tracking number
            textarea.clear()
            textarea.send_keys(cargo_tracking_number)

            self.show_message("Success", f"Entered cargoTrackingNumber: {cargo_tracking_number}")
        except Exception as e:
            self.show_message("Error", f"An error occurred while entering cargoTrackingNumber: {str(e)}")

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
