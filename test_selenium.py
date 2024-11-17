from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_selenium():
    try:
        print("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        print("Installing ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        print(f"ChromeDriver path: {driver_path}")

        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(driver_path),
            options=chrome_options
        )

        print("Testing with a simple URL...")
        driver.get("https://www.google.com")
        print("Title:", driver.title)

        driver.quit()
        print("Test successful!")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    test_selenium()
