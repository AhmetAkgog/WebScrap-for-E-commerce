# WebScrap-for-E-commerce

The aim of this project is to scrape product data from an e-commerce website and upload it to Trendyol Marketplace using Trendyol's API service. It takes login information for the specified website and manages cookies across pages. MANDATORY parts are highlighted in caps. This code is specifically designed for the website (https://www.yeninesiltoptanci.com/), so make sure to change the variable names according to your target website. Especially getting Color and Size values was strange and more difficult than average.

Update on 25/09: Now it can extract order data from trendyol with API then create orders in the website. Check OtoSiparis.py
Dependencies: BeautifulSoup, Selenium, PyQt5, mysql.connector, OS is Win11, Chrome Webdriver (Webdrivers version should be compatible with your Chrome browser, My Chrome version: Version 129.0.6668.60)

Update on 14/11: Added new .py file that creates products in the trendyol website one by one automated. It takes inputs like id,password,product id etc. Before running it change profile_path to your personal chrome profile. That profile should have an access to your Trendyol Account, to achieve this enter the website manually 1 or 2 times in the automation tab.

Webdrivers Download Link: https://googlechromelabs.github.io/chrome-for-testing/#dev
Trendyol Marketplace API Documentation Link : https://developers.trendyol.com/int/
