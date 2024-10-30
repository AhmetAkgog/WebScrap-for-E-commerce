from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_extension('C:/Users/ahmet/Desktop/Yazılım/VSCode_Projects/Datascrap for Trendyol API/CJPALHDLNBPAFIAMEJDNHCPHJBKEIAGM_1_59_0_0.crx') #ublock origin extension
profile_path = r"C:\Users\ahmet\AppData\Local\Google\Chrome\User Data\Profile 1"
chrome_options.add_argument(f"user-data-dir={profile_path}")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Set up the Chrome driver
service = Service(executable_path='C:/Users/ahmet/Desktop/Yazılım/chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=service, options=chrome_options)

# Hide webdriver property
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Open the login page
driver.get('https://partner.trendyol.com/account/login')

# Wait until the dashboard is loaded or timeout
try:
    WebDriverWait(driver, 30).until(EC.url_contains('dashboard'))
except Exception:
    print("Dashboard did not load within the expected time.")


time.sleep(5)

# Open a new tab for the second login
driver.execute_script("window.open('');")
time.sleep(1)
driver.switch_to.window(driver.window_handles[1])
driver.get('https://www.yeninesiltoptanci.com/UyeGiris')

# Login to the second site
username = "your username"
password = "your password"
merchant_sku = ["15003", "15010"]
Category = "Elbise"
ModelKodu = "test1"
Brand = "VSNL"

try:
    driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(username)
    driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(password)
    driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click()
except Exception as e:
    print(f"Error during login: {e}")

time.sleep(10)
# Search and interact with merchant SKU input
for i in merchant_sku:
    try:
        merchant_sku_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "txtbxArama"))
        )
        # Clear any previous input and enter the new merchant SKU
        merchant_sku_input.clear()
        merchant_sku_input.send_keys(i)
        # Wait for the search button to be clickable and click it
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnKelimeAra"))
        )
        search_button.click()

        product_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "productName.detailUrl"))
        )
        product_link.click()
    except Exception as e:
        print(f"Error interacting with merchant SKU elements: {e}")

    # Extract productDetailModel from page source
    page_source = driver.page_source
    match = re.search(r'var productDetailModel = ({.*?});', page_source, re.DOTALL)
    if match:
        product_detail_model = json.loads(match.group(1))
        original_product_name = product_detail_model.get('productName', '')
        print(f"Original Product Name: {original_product_name}")
    else:
        print("Could not find the productDetailModel variable in the HTML.")

    # Switch back to the first tab and interact with Trendyol product page
    driver.switch_to.window(driver.window_handles[0])
    driver.get("https://partner.trendyol.com/products/single-product")

    try:
        trendyol_product_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Ürün adı giriniz"]')) #Trendyola ürün ismini giriyor
        )
        trendyol_product_name.send_keys(original_product_name)

        reset_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"Ürün Bilgileri")]')) #Ürün bilgilerine tıklayıp dropdownu kapatıyor
        )
        reset_button.click()

        # Select category
        time.sleep(5)
        category_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "input-container")) #Kategori kutusuna tıklayıp dropdownu açıyor
        )
        category_box.click()

        category_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#select-category .form-control")) 
        )
        category_input.clear()
        category_input.send_keys(Category) #Kategori ismini giriyor

        trendyol_category_click = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//li[normalize-space(text())="{Category}"]')) #Trendyola kategori ismini giriyor
        )
        trendyol_category_click.click()


        time.sleep(2)

        reset_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"Ürün Bilgileri")]')) #Ürün bilgilerine tıklayıp dropdownu kapatıyor
        )
        reset_button.click()

        time.sleep(5)

        trendyol_model_kodu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Model kodu giriniz"]')) #Model kodu kutusuna model kodunu giriyor
        )
        trendyol_model_kodu.send_keys(ModelKodu)
        
        time.sleep(2)

        marka_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//p[contains(text(),"Marka seçiniz")]')) #Marka kutusuna tıklayıp dropdownu açıyor
        )
        marka_box.click()

        time.sleep(2)

        trendyol_Brand = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Arama"]')) #Sends brand keys to box
        )
        trendyol_Brand.send_keys(Brand)

        time.sleep(2)

        brand_output = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//span[contains(text(),"{Brand}")]')) #Chooses the outcome in the dropdown
        )
        brand_output.click()

        reset_button2 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"Ürün Özellikleri")]')) #Ürün bilgilerine tıklayıp dropdownu kapatıyor
        )
        reset_button2.click()


    except Exception as e:
        print(f"Error interacting with Trendyol elements: {e}")
    
    driver.switch_to.window(driver.window_handles[1])


# Optional: Verify and print cookies
cookies = driver.get_cookies()
for cookie in cookies:
    print(f"Name: {cookie['name']}, Value: {cookie['value']}")

# Close the browser
time.sleep(60)
driver.quit()

