import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from urllib.parse import urljoin
import requests

# Setup WebDriver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    service = Service('YOUR WEBDRIVERS.EXE PATH')  # Update the path to your ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Login function
def login(driver, login_url, username, password):
    driver.get(login_url)
    
    # Fill in the login form
    driver.find_element(By.NAME, "txtUyeGirisEmail").send_keys(username) # Update the name of the email input field according to the target website
    driver.find_element(By.NAME, "txtUyeGirisPassword").send_keys(password) # Update the name of the password input field according to the target website
    
    # Submit the form
    driver.find_element(By.CLASS_NAME, "uyeGirisFormDetailButtonList").click() # Update the name of the click button field according to the target website
    
    time.sleep(5)  # Wait for login to complete
    
    # Check if login was successful
    if "ENTER A TEXT ONLY APPEARS WHEN LOGGED IN SOMETHING LIKE USERNAME ETC." in driver.page_source:
        print("Login successful")
    else:
        print("Login failed")
        driver.quit()
        exit()

def get_cookies(driver):
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict

def get_page_html(url, cookies, timeout=40):
    session = requests.Session()
    session.cookies.update(cookies)
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
# Get product URLs from dynamic scrolling page
def get_product_urls(driver, url, max_scrolls=10):
    driver.get(url)
    
    # Scroll to load more products
    for _ in range(max_scrolls):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(3)  # Wait for new content to load
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract product URLs
    product_links = [a for a in soup.find_all('a') if 'detailUrl' in a.get('class', []) and len(a.get('class', [])) == 1]
    product_urls = [urljoin(url, link.get('href')) for link in product_links]
    
    return product_urls

def get_page_html(url, cookies=None,timeout=40):
    try:
        # If cookies are provided, use them in the request
        if cookies:
            response = requests.get(url, cookies=cookies, timeout=timeout)
        else:
            response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def scrape_product_pages(product_urls, cookies, delay=2):
    all_html = []
    
    for url in product_urls:
        html = get_page_html(url, cookies=cookies)  # Pass cookies here
        if html:
            all_html.append(html)
            print(f"Successfully retrieved {url}")
        else:
            print(f"Failed to retrieve {url}")
        
        time.sleep(delay)  # Add a delay between requests
    
    return all_html

def extract_product_data(html, start_barcode, previous_product_name=None, color_suffix=1):
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
        product_name = product_name.replace('YNT', 'THE NAME YOU WANT TO REPLACE')

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
        print(product.get('urunFiyatiOrjinal')) #To check if the driver is logged in or not. It returns different values if not logged in.
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

def send_product_data_to_trendyol(batched_data, supplier_id, access_token):
    url = f"https://api.trendyol.com/sapigw/suppliers/{supplier_id}/v2/products"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "200300444 - Trendyolsoft",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=batched_data)
    
    if response.status_code == 200:
        try:
            response_data = response.json()
            batch_request_id = response_data.get("batchRequestId", "No batch request ID found")
            print(f"Batch Request ID: {batch_request_id}")
        except json.JSONDecodeError:
            print("Failed to parse JSON response.")
    else:
        print(f"Failed to send product data. Status code: {response.status_code}")
        try:
            error_details = response.json()
            print(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text}")

def main():
    login_url = "ENTER LOGIN URL"  # Replace with your login URL
    username = "ENTER USERNAME"  # Replace with your username
    password = "ENTER PASSWORD"  # Replace with your password

    driver = setup_driver()
    
    # Log in to the website
    login(driver, login_url, username, password)
    
    cookies = get_cookies(driver)

    base_urls = [
        'https://www.yeninesiltoptanci.com/fantezi-kostum', #Enter URL that lists Products
        'https://www.yeninesiltoptanci.com/jartiyer-takim'
    ]

    all_product_data = []
    start_barcode = 645222333
    previous_product_name = None
    color_suffix = 1

    print(driver.get_cookies())

    for base_url in base_urls:

        product_urls = get_product_urls(driver, base_url)
        
        if not product_urls:
            print(f"No product URLs found for {base_url}.")
            continue
        
        all_html = scrape_product_pages(product_urls, cookies, delay=2)
        
        for html in all_html:
            product_data, start_barcode, previous_product_name, color_suffix = extract_product_data(html, start_barcode, previous_product_name, color_suffix)
            all_product_data.extend(product_data)
    
    driver.quit()
    
    formatted_data = {
        "items": all_product_data
    }

    json_output = json.dumps(formatted_data, indent=2, ensure_ascii=False)

    with open("product_data.json", "w", encoding="utf-8") as f:
        f.write(json_output)

    batch_size = 1 # Trendyol takes a maximum of 50 products per 10 seconds manage your batch size according to this info
    supplier_id = "ENTER SELLER ID"
    access_token = "ENTER ACCESS TOKEN"

    for i in range(0, len(all_product_data), batch_size):
        batch = all_product_data[i:i + batch_size]
        batched_data = {"items": batch}
        
        send_product_data_to_trendyol(batched_data, supplier_id, access_token)
        
        time.sleep(3) # Trendyol takes a maximum of 50 products per 10 seconds manage your batch size according to this info

if __name__ == "__main__":
    main()