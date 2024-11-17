from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fastapi.staticfiles import StaticFiles
import csv
from io import StringIO
import json
from datetime import datetime
import os

app = FastAPI(title="DFM Stock API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Disposition", "Access-Control-Allow-Origin"],
    max_age=3600
)

# Create a 'static' directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class StockData(BaseModel):
    symbol: str
    price: float
    change: float
    change_percentage: str

class StocksResponse(BaseModel):
    stocks: List[StockData]

def parse_change_values(change_text):
    """
    Parses the change text to extract change value and percentage.
    """
    lines = change_text.strip().split('\n')
    change_value = lines[0].replace(' ', '')
    change_percentage = lines[1].replace(' ', '')
    return change_value, change_percentage

def get_stock_data_selenium(symbol: str) -> dict:
    """
    Fetches data from DFM website using Selenium.
    """
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Initialize Chrome driver with explicit path
        driver_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(
            service=Service(driver_path),
            options=chrome_options
        )

        # Set page load timeout
        driver.set_page_load_timeout(20)
        
        url = f"https://www.dfm.ae/the-exchange/market-information/company/{symbol}/trading/trading-summary"
        print(f"Fetching data from: {url}")  # Debug log
        
        driver.get(url)
        driver.implicitly_wait(10)  # Increased wait time

        # Wait for elements with explicit wait
        wait = WebDriverWait(driver, 15)
        price_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='__layout']/div/div[3]/section[1]/div/div/div[3]/div/div[2]"))
        )
        print(f"Found price element for {symbol}")  # Debug log

        change_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='__layout']/div/div[3]/section[1]/div/div/div[3]/div/div[3]"))
        )
        print(f"Found change element for {symbol}")  # Debug log

        price = price_element.text.strip()
        change_text = change_element.text.strip()
        
        print(f"Raw data for {symbol}: Price={price}, Change={change_text}")  # Debug log
        
        change_value, change_percentage = parse_change_values(change_text)

        if driver:
            driver.quit()
        
        return {
            "symbol": symbol,
            "price": float(price),
            "change": float(change_value.replace('+', '')),
            "change_percentage": change_percentage
        }

    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")  # Debug log
        if driver:
            driver.quit()
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data for {symbol}: {str(e)}"
        )

@app.get("/")
async def root():
    """Serve the index.html file"""
    return FileResponse('index.html')

@app.get("/api/v1/stocks", response_model=StocksResponse)
async def get_stocks():
    """Get data for all supported stocks"""
    stocks = ['SALIK', 'DTC']
    results = []
    
    for symbol in stocks:
        data = get_stock_data_selenium(symbol)
        if data:
            results.append(data)
    
    return {"stocks": results}

@app.get("/api/v1/stocks/raw")
async def get_stocks_raw():
    """Get raw stock data in flat JSON format"""
    try:
        # Reuse the working endpoint logic
        stocks_response = await get_stocks()
        
        # Transform the data into the raw format
        results = []
        for stock in stocks_response["stocks"]:
            results.append({
                "Symbol": stock["symbol"],
                "Price": float(stock["price"]),
                "Change": float(stock["change"]),
                "ChangePercentage": float(stock["change_percentage"].replace('%', '').replace('+', '')),
                "LastUpdate": datetime.now().isoformat()
            })

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
            "X-Data-Timestamp": datetime.now().isoformat()
        }

        return JSONResponse(
            content={"stocks": results},
            headers=headers
        )

    except Exception as e:
        print(f"Error generating raw data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating raw data: {str(e)}"
        )

@app.get("/api/v1/stocks/mstr")
async def get_stocks_mstr():
    """Get stock data in MicroStrategy-friendly format"""
    try:
        # Reuse the working endpoint logic
        stocks_response = await get_stocks()
        
        # Transform data for MicroStrategy
        data_rows = []
        for stock in stocks_response["stocks"]:
            data_rows.append([
                stock["symbol"],                                           # Symbol
                float(stock["price"]),                                    # Price
                float(stock["change"]),                                   # Change
                float(stock["change_percentage"].replace('%', '').replace('+', ''))  # Change%
            ])

        mstr_response = {
            "name": "DFM Stocks Data",
            "columns": [
                {"name": "Symbol", "dataType": "string"},
                {"name": "Price", "dataType": "double"},
                {"name": "Change", "dataType": "double"},
                {"name": "ChangePercentage", "dataType": "double"}
            ],
            "data": data_rows
        }

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cache-Control": "no-cache",
            "X-Data-Timestamp": datetime.now().isoformat()
        }

        return JSONResponse(
            content=mstr_response,
            headers=headers
        )
    
    except Exception as e:
        print(f"Error generating MicroStrategy data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating MicroStrategy data: {str(e)}"
        )

@app.get("/api/v1/stocks/csv")
async def get_stocks_csv():
    """Get stock data in CSV format"""
    try:
        # Reuse the working endpoint logic
        stocks_response = await get_stocks()
        
        # Transform the data into CSV format
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Symbol', 'Price (AED)', 'Change', 'Change %', 'Last Update'])
        
        # Write data
        for stock in stocks_response["stocks"]:
            writer.writerow([
                stock["symbol"],
                float(stock["price"]),
                float(stock["change"]),
                float(stock["change_percentage"].replace('%', '').replace('+', '')),
                datetime.now().isoformat()
            ])
        
        headers = {
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename=dfm_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cache-Control": "no-cache"
        }
        
        return PlainTextResponse(
            output.getvalue(),
            headers=headers,
            media_type="text/csv"
        )

    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating CSV: {str(e)}"
        )

@app.get("/api/v1/stocks/csv/simple", response_class=PlainTextResponse)
async def get_stocks_csv_simple():
    """Get simplified stock data in CSV format for MicroStrategy"""
    try:
        stocks_response = await get_stocks()
        
        # Create CSV content directly as a string
        csv_content = "Symbol,Price (AED),Change,Change %,Last Update\n"
        
        for stock in stocks_response["stocks"]:
            csv_content += f"{stock['symbol']},"
            csv_content += f"{stock['price']},"
            csv_content += f"{stock['change']},"
            csv_content += f"{stock['change_percentage'].replace('%', '')},"
            csv_content += f"{datetime.now().isoformat()}\n"
        
        return PlainTextResponse(
            content=csv_content,
            media_type="text/plain",
            headers={
                "Content-Type": "text/plain",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stocks/data")
async def get_stocks_data():
    """Get stock data in a very simple format"""
    try:
        stocks_response = await get_stocks()
        
        # Create a simple table structure
        data = {
            "columnHeaders": ["Symbol", "Price", "Change", "ChangePercentage"],
            "rows": []
        }
        
        for stock in stocks_response["stocks"]:
            data["rows"].append([
                stock["symbol"],
                str(stock["price"]),
                str(stock["change"]),
                stock["change_percentage"].replace('%', '')
            ])

        return JSONResponse(
            content=data,
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 