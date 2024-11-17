from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

def parse_change_values(change_text):
    """
    Parses the change text to extract change value and percentage.
    
    Args:
        change_text (str): Combined change text (e.g., '-0.060\n-1.122%' or '+ 0.050\n+ 1.89%')
        
    Returns:
        tuple: (change_value, change_percentage)
    """
    lines = change_text.strip().split('\n')
    change_value = lines[0].replace(' ', '')
    change_percentage = lines[1].replace(' ', '')
    return change_value, change_percentage

def get_stock_data_selenium(symbol):
    """
    Fetches data from DFM website using Selenium.
    
    Args:
        symbol (str): Stock symbol (e.g., 'SALIK' or 'DTC')

    Returns:
        dict: Dictionary containing the stock data
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        url = f"https://www.dfm.ae/the-exchange/market-information/company/{symbol}/trading/trading-summary"
        driver.get(url)
        driver.implicitly_wait(5)

        price_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='__layout']/div/div[3]/section[1]/div/div/div[3]/div/div[2]"))
        )

        change_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='__layout']/div/div[3]/section[1]/div/div/div[3]/div/div[3]"))
        )

        price = price_element.text.strip()
        change_text = change_element.text.strip()
        change_value, change_percentage = parse_change_values(change_text)

        driver.quit()
        
        return {
            "symbol": symbol,
            "price": float(price),
            "change": float(change_value.replace('+', '')),
            "change_percentage": change_percentage
        }

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

if __name__ == "__main__":
    stocks = ['SALIK', 'DTC']
    results = []
    
    for symbol in stocks:
        data = get_stock_data_selenium(symbol)
        if data:
            results.append(data)
    
    # Convert to JSON and print
    print(json.dumps({"stocks": results}, indent=2))