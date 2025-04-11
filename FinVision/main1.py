from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

# Define Pydantic model for request validation
class BillData(BaseModel):
    text: str

# Function to classify extracted products from OCR text
def extract_and_classify_products(text: str):
    categories = {
        "Food": ["BREAD", "EGGS", "COTTAGE CHEESE", "YOGURT", "TOMATOES", "BANANAS", "CHICKEN"],
        "Beverages": ["MILK", "COFFEE", "JUICE", "WATER", "TEA", "SODA", "WINE", "BEER"],
        "Snacks": ["CRACKERS", "COOKIES", "CHOCOLATE", "CANDY", "CHIPS", "NUTS", "SEEDS"],
    }

    lines = text.strip().split('\n')
    product_list = []

    for line in lines:
        words = line.split()
        for i, word in enumerate(words):
            if word.replace('.', '', 1).isdigit():  # Detect price
                price = float(word.replace('$', '').replace(',', ''))
                product_name = ' '.join(words[:i]).strip()

                # Determine product category
                product_category = "Others"
                for category, keywords in categories.items():
                    if any(keyword in product_name.upper() for keyword in keywords):
                        product_category = category
                        break

                product_list.append({"name": product_name, "price": price, "category": product_category})

    return product_list

# Function to extract total amount
def extract_final_amount_from_total(text: str):
    lines = text.strip().split('\n')
    total_keywords = ["TOTAL", "FINAL AMOUNT", "PAYMENT", "BALANCE DUE"]

    for line in reversed(lines):
        if any(keyword in line.upper() for keyword in total_keywords):
            words = line.split()
            for word in words:
                if word.replace('$', '').replace(',', '').isdigit():
                    return float(word.replace('$', '').replace(',', ''))

    return None

# API endpoint to process bill text
@app.post("/process_bill/")
def process_bill(bill: BillData):
    classified_products = extract_and_classify_products(bill.text)
    final_amount = extract_final_amount_from_total(bill.text)

    return {
        "classified_products": classified_products,
        "total_amount": final_amount if final_amount is not None else "Not Found"
    }
