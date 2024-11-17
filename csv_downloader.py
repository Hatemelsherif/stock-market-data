import requests
import schedule
import time
import os
from datetime import datetime
import sys

def download_csv():
    try:
        url = "http://localhost:8000/api/v1/stocks/csv/simple"
        response = requests.get(url, timeout=10)
        
        # Ensure static directory exists
        os.makedirs("static", exist_ok=True)
        
        # Save the CSV file
        with open("static/stocks.csv", "w") as f:
            f.write(response.text)
            
        print(f"CSV updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except requests.exceptions.ConnectionError:
        print("API server not available. Retrying...")
        return False
    except Exception as e:
        print(f"Error downloading CSV: {str(e)}")
        return False

def main():
    try:
        print("Starting CSV downloader...")
        print("Waiting for API server to be available...")
        
        # Keep trying initial download until successful
        while not download_csv():
            time.sleep(5)
            
        print("API server connected successfully!")
        
        # Schedule downloads every 5 minutes
        schedule.every(5).minutes.do(download_csv)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping CSV downloader...")
        sys.exit(0)
    except Exception as e:
        print(f"Error in main loop: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 