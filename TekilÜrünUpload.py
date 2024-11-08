from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import re
import json
import time
import random
import string

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
    WebDriverWait(driver, 2).until(EC.url_contains('dashboard'))
except Exception:
    print("Dashboard did not load within the expected time.")


time.sleep(5)

# Open a new tab for the second login
driver.execute_script("window.open('');")
time.sleep(1)
driver.switch_to.window(driver.window_handles[1])
driver.get('https://www.yeninesiltoptanci.com/UyeGiris')

# Login to the second site
username = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
merchant_sku = ["15003","15019","15706"]
Category = "Elbise"
ModelKodu = "test1"
Brand = "VSNL"
Kar_marjı = 0.5

try:
    driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(username)
    driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(password)
    driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click()
except Exception as e:
    print(f"Error during login: {e}")

time.sleep(10)
color_count = 1
shippingFee = 61.9
hizmetbedeli = 8.39
commissionRate = 0.215
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
        products = product_detail_model.get('products', []) #Gets the details of the product
        print(products)

        original_product_name = product_detail_model.get('productName', '')
        print(f"Original Product Name: {original_product_name}")

        tedarikci_values = [(item['tedarikciKodu'].split('|'),item.get("stokKodu"),item.get("stokAdedi"),item.get("urunFiyatiOrjinal"),item.get("urunFiyatiOrjinalKDV")) for item in products]
        print(tedarikci_values)
        color = tedarikci_values[0][0][2] 
        if color == "MAVİ" or color == "SİYAH":
            color_mapping = { #Türkçe İngilizcedeki büyük İ farkından dolayı else teki block doğru çalışmıyor ve küçük i olsa bile olmuyor
            "MAVİ": "Mavi",
            "SİYAH": "Siyah"
        }
            color = color_mapping.get(color, color.lower())
        else:
            color = color[0].upper() + color[1:].casefold()


        if color == "Saks":
            color = "Mavi"
        elif color == "Lila":
            color = "Mor"
        elif color == "Fuşya" or color == "Pudra":
            color = "Pembe"

        fiyat = tedarikci_values[0][3]+tedarikci_values[0][4]
        satis_fiyati = (fiyat + shippingFee + hizmetbedeli)*(1+Kar_marjı)/(1-commissionRate)
        whole_part = int(satis_fiyati)
        decimal_part = ",90"
        formatted_price = f"{whole_part}{decimal_part}"
        print(f"Color: {color}")
        print(f"Fiyat: {fiyat}",f"Satis Fiyati: {satis_fiyati}")
        
        size_list = []
        stok_kodu_list = []
        stok_adedi_list = []
        for i in tedarikci_values:
            size_list.append(i[0][3])
            stok_kodu_list.append(i[1])
            stok_adedi_list.append(i[2])
        print(f"Size List: {size_list}",f"Stok Kodu List: {stok_kodu_list}",f"Stok Adedi List: {stok_adedi_list}")


    else:
        print("Could not find the productDetailModel variable in the HTML.")

    # Switch back to the first tab and interact with Trendyol product page
    driver.switch_to.window(driver.window_handles[0])
    driver.get("https://partner.trendyol.com/products/single-product")
    driver.execute_script("document.body.style.zoom='80%'")
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

        Urun_ozellikleri_baslik = driver.find_element(By.XPATH, '//h4[contains(text(),"Ürün Özellikleri")]') #Scrolls to Urun Ozellikleri Headline
        driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", Urun_ozellikleri_baslik)


        if Category == "String":
            kumas_tipi_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Kumaş Tipi"]'))
            )
            kumas_tipi_element.click()

            dantel_secenek = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[normalize-space(text())="Dantel"]'))
            )
            dantel_secenek.click()
        elif Category == "Elbise":
            boy = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Boy"]'))
            )
            boy.click()
            boy_secenek = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[normalize-space(text())="167"]'))
            )
            boy_secenek.click()
            ####
            kumas_tipi_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Kumaş Tipi"]'))
            )
            kumas_tipi_element.click()

            dantel_secenek = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[normalize-space(text())="Tül"]'))
            )
            dantel_secenek.click()
            ####
            kalıp_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Kalıp"]'))
            )
            kalıp_element.click()

            kalıp_search = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[4]/div/div[2]/div[1]/div[2]/div/div/div/div/div/div/div[2]/div[1]/div/div/div/div/input')) #Sends brand keys to box
            )
            time.sleep(2)
            kalıp_search.send_keys("Belirtilmemiş")
            time.sleep(2)
            # Try locating the "Belirtilmemiş" option
            option = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[4]/div/div[2]/div[1]/div[2]/div/div/div/div/div/div/div[2]/div[2]/span'))
            )
            option.click()

            yas_grubu_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Yaş Grubu"]'))
            )
            yas_grubu_element.click()

            yetiskin_secenek = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[normalize-space(text())="Yetişkin"]'))
            )
            yetiskin_secenek.click()

        

        urun_acıklaması = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[1]/div/div[4]/div/span')) #Soldaki ürün açıklaması kısmına tıklıyor
        )
        urun_acıklaması.click()

        time.sleep(2)
        ai_acıklama_buton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[6]/div/div/div/div/div[2]/header/button')) #AI açıklama butonuna tıklıyor
        )
        ai_acıklama_buton.click()

        time.sleep(2)

        aciklama_onayla = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[6]/div/div[2]/div[2]/div/div[3]/div/button[2]')) #AI açıklamayı onaylıyor
        )
        aciklama_onayla.click()

        time.sleep(1)

        satis_bilgileri = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[1]/div/div[5]/div/span')) #clicks satış bilgileri on the left
        )
        satis_bilgileri.click()
        
        time.sleep(3)

        renk_skalası = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[2]/div[1]/div/div/div/div[1]/div[1]/div/div')) #clicks satış bilgileri on the left
        )
        renk_skalası.click()

        time.sleep(3)

        # Define the target color text you want to click
          # Update this to the color you want to select
        target_color = color

        dropdown_area = driver.find_element(By.CLASS_NAME, "s-content")

        # Initialize a flag to control the loop
        found = False

        # Scroll and search until the target color is found or max attempts are reached
        for _ in range(20):  # Limit the number of scrolls to prevent infinite loop
            # Locate all items in the dropdown again
            items = driver.find_elements(By.CSS_SELECTOR, ".s-content .item")

            for item in items:
                color_text = item.find_element(By.CLASS_NAME, "text").text

                # Check if this item matches the target color
                if color_text == target_color:
                    # Scroll to the item
                    ActionChains(driver).move_to_element(item).perform()
                    time.sleep(0.2)  # Small delay for smoother scrolling

                    # Click the item if it matches and break the loop
                    item.click()
                    print(f"Clicked on color: {color_text}")
                    found = True
                    break
                
            # Exit outer loop if item was found
            if found:
                break
            
            # If target not found, scroll down further
            dropdown_area.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.5)  # Delay for smooth scrolling

        if not found:
            print("Target color not found in dropdown.")


        renk_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[2]/div[1]/div/div/div/div[1]/div[2]/div/div/div/input')) #Sends color keys to box
        )
        renk_input.clear()
        renk_input.send_keys(f"{color}"+f"{color_count}")
        color_count += 1

        Renk_Ekle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[2]/div[1]/div/div/div/div[1]/button/div')) #clicks size input box
        )
        Renk_Ekle.click()

        Beden_Skalası = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[2]/div[2]/div/div[1]/div/div/div')) #clicks size input box
        )
        Beden_Skalası.click()

        for i in size_list:
            beden_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/input')) #Sends size keys to box
            )
            beden_input.send_keys(i)
            size_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[contains(@class, 'text') and text()='{i}']"))
            )
            size_checkbox.click()
            beden_input.clear()
        
        satış_bilgileri = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[1]/div/div[5]/div/span')) #clicks size input box
        )
        satış_bilgileri.click()

        time.sleep(2)

        satis_fiyati_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[3]/div/div/div[1]/div/div/div/div/div/div/input')) #Sends size keys to box
        )
        satis_fiyati_input.send_keys(Keys.HOME)
        satis_fiyati_input.send_keys(formatted_price) # BURAYLA UĞRAŞ

        kdv_rate = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[3]/div/div/div[2]/div/div/div/div/div')) #clicks size input box
        )
        kdv_rate.click()

        kdv_10 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[3]/div/div/div[2]/div/div/div/div/div/div/div[3]/span')) #clicks size input box
        )
        kdv_10.click()

        time.sleep(3)

        all_checkbox = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[4]/div[1]/table/thead/tr/th[1]/div/label')) #clicks size implement to all checkbox
        )
        all_checkbox.click()

        tümüne_uygula = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[3]/div/div/div[4]/button/div')) #clicks to tümüne uygula button
        )
        tümüne_uygula.click()

        Image_Upload_Button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[4]/div[1]/table/tbody/tr[1]/td[2]/div/div/div')) #clicks to tümüne uygula button
        )
        Image_Upload_Button.click()

        file_paths = [
        r"C:\Users\ahmet\Desktop\İş\1 Özel Bölgesi Açık Seri Toplu\15003 Serisi\15003 - Siyah\15003.jpg",
        r"C:\Users\ahmet\Desktop\İş\1 Özel Bölgesi Açık Seri Toplu\15003 Serisi\15003 - Siyah\150032.jpg",
        r"C:\Users\ahmet\Desktop\İş\1 Özel Bölgesi Açık Seri Toplu\15003 Serisi\15003 - Siyah\150033.jpg"
        ]

        file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[5]/div[2]/div/div[2]/div[2]/div[1]/div[1]/input"))
        )

        for file_path in file_paths:
            file_input.send_keys(file_path)

        Görselleri_Yükle_Button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[2]/div[8]/div/div[5]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button[2]')) #popup görselleri yükle butonu
        )

        time.sleep(3)
        Görselleri_Yükle_Button.click()

        # Generate a random alphanumeric value
        def generate_random_value(length=8):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        # Locate elements with a partial match
        barcode_fields = driver.find_elements(By.XPATH, "//input[contains(@name, 'barcode')]")

        for field in barcode_fields:
            random_value = generate_random_value()
            field.send_keys(random_value)


        stok_fields = driver.find_elements(By.XPATH, "//input[contains(@name, 'quantity')]")

        stok_index = 0

        # Iterate through the found fields and send stock values to each one, excluding the 4th input field
        for field in stok_fields:
            # Skip the field with name 'bulkUpdate_quantity' (1st input)
            if field.get_attribute("name") == "bulkUpdate_quantity":
                print(f"Skipping field with name '{field.get_attribute('name')}'.")
                continue
            
            # Ensure there's still a stock value left to assign
            if stok_index < len(stok_adedi_list):
                field.send_keys(str(stok_adedi_list[stok_index]))
                print(f"Sent value '{stok_adedi_list[stok_index]}' to field {stok_index+1}")
                stok_index += 1  # Move to the next stock value
            else:
                print("No more stock values to send.")


        stock_code_fields = driver.find_elements(By.XPATH, "//input[contains(@name, 'stockCode')]")

        for i,field in enumerate(stock_code_fields):
            field.send_keys(stok_kodu_list[i])
        
        time.sleep(3)

        Ürünü_Onaya_Gönder_Button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[2]/footer/div/button')) #en sondaki ürünü onaya gönder butonu
        )

        Ürünü_Onaya_Gönder_Button.click()
        
        Yoksay_ve_Devamet_Button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[3]/div[2]/div/div[2]/div/div[3]/button[1]')) #ürünü onaya göndere basınca çıkan popupdaki yoksay ve devam et butonu
        )

        Yoksay_ve_Devamet_Button.click()

        time.sleep(3)


    except Exception as e:
        print(f"Error interacting with Trendyol elements: {e}")
    
    driver.switch_to.window(driver.window_handles[1])


# Optional: Verify and print cookies


# Close the browser
time.sleep(60)
driver.quit()

#Ürün bazında özellikleri seçmek istersen böyle yap, normalde kategori bazında yapıyorum, Urun_ozellikleri_baslik variable ından sonra yapıştır
"""if i == "15003": #
    kumas_tipi_element = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@data-vv-as="Kumaş Tipi"]'))
    )
    kumas_tipi_element.click()
    dantel_secenek = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '//span[normalize-space(text())="Dantel"]'))
    )
    dantel_secenek.click()"""

#Ürün özelliklerine gelmek için alternatif, direkt soldan tıklıyor
"""        alternative_urun_ozellikleri = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/div[1]/div/div[3]/div/span')) #Chooses the outcome in the dropdown
        )
        alternative_urun_ozellikleri.click()"""


