# WebScrap-for-E-commerce

The aim of this project is to scrape product data from an e-commerce website and upload it to Trendyol Marketplace using Trendyol's API service. It takes login information for the specified website and manages cookies across pages. MANDATORY parts are highlighted in caps. This code is specifically designed for the website (https://www.yeninesiltoptanci.com/), so make sure to change the variable names according to your target website. Especially getting Color and Size values was strange and more difficult than average.
Update on 25/09: Now it can extract order data from trendyol with API then create orders in the website. Check OtoSiparis.py
Dependencies: BeautifulSoup, Selenium, PyQt5, mysql.connector, OS is Win11, Chrome Webdriver (Webdrivers version should be compatible with your Chrome browser, My Chrome version: Version 127.0.6533.120)

Webdrivers Download Link: https://googlechromelabs.github.io/chrome-for-testing/#dev
Trendyol Marketplace API Documentation Link : https://developers.trendyol.com/int/
