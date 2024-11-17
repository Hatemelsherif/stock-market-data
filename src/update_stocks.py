import requests
from datetime import datetime
import os
import sys

def get_stock_data():
    """Fetch stock data from your API"""
    try:
        # Replace with your actual API endpoint
        url = "https://your-api-url/api/v1/stocks"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

def format_csv(data):
    """Format the data as CSV"""
    csv_lines = ["Symbol,Price (AED),Change,Change %,Last Update"]
    
    for stock in data["stocks"]:
        line = (
            f"{stock['symbol']},"
            f"{stock['price']},"
            f"{stock['change']},"
            f"{stock['change_percentage'].replace('%', '')},"
            f"{datetime.now().isoformat()}"
        )
        csv_lines.append(line)
    
    return "\n".join(csv_lines)

def save_csv(content):
    """Save the CSV file"""
    os.makedirs("data", exist_ok=True)
    with open("data/stocks.csv", "w") as f:
        f.write(content)

def main():
    print("Fetching stock data...")
    data = get_stock_data()
    
    print("Formatting CSV...")
    csv_content = format_csv(data)
    
    print("Saving CSV...")
    save_csv(csv_content)
    
    print("Update complete!")

if __name__ == "__main__":
    main() 