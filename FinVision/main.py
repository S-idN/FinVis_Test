from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

# Define Pydantic model for request validation
class BillData(BaseModel):
    text: str  


def extract_and_classify_products(text):
    """
    This function extracts products and their prices from the bill and classifies them into categories.
    It returns a list of classified products with their price.
    """
    # Define product categories
    categories = {
    "Food": [
        "BREAD", "EGGS", "COTTAGE CHEESE", "YOGURT", "TOMATOES", "BANANAS", "CHICKEN", 
        "TUNA", "VEGETABLES", "FRUIT", "POTATOES", "CARROTS", "LETTUCE", "PUMPKIN", "CABBAGE",
        "ONIONS", "GARLIC", "PEAS", "APPLE", "ORANGE", "PEACH", "STRAWBERRY"
    ],
    "Beverages": [
        "MILK", "COFFEE", "JUICE", "WATER", "TEA", "SODA", "ENERGY DRINK", "SPORTS DRINK", 
        "ALCOHOL", "WINE", "BEER", "COCKTAIL", "CIDER"
    ],
    "Household": [
        "TOILET PAPER", "WIPES", "CLEANER", "PAPER TOWELS", "SPONGE", "MOP", "GLOVES", 
        "DISINFECTANT", "DISH SOAP", "LAUNDRY DETERGENT", "BROOM", "MOP", "TRASH BAGS", 
        "FABRIC SOFTENER", "AIR FRESHENER", "TISSUES", "PLASTIC WRAP", "ALUMINUM FOIL"
    ],
    "Snacks": [
        "CRACKERS", "COOKIES", "CHOCOLATE", "CANDY", "CANDY BAR", "CHIPS", "NUTS", "SEEDS",
        "CORN SNACKS", "TRAIL MIX", "PRETZELS", "POP CORN", "GUM", "JELLY BEANS", "GUMMY BEARS"
    ],
    "Dairy": [
        "CHEESE", "BUTTER", "MILK", "YOGURT", "ICE CREAM", "CREAM", "COTTAGE CHEESE", 
        "WHIPPED CREAM", "SOUR CREAM", "EGGS"
    ],
    "Frozen": [
        "ICE CREAM", "FROZEN FOOD", "FROZEN PIZZA", "FROZEN VEGETABLES", "FROZEN FRUITS", 
        "FROZEN MEALS", "FROZEN DINNER", "FROZEN FRENCH FRIES", "FROZEN BURGERS", "FROZEN CHICKEN"
    ],
    "Bakery": [
        "BREAD", "BAGELS", "CROISSANT", "MUFFINS", "DONUTS", "PASTRY", "CAKE", "PIE", "BISCUIT", 
        "CUPCAKES", "COOKIES", "TARTS"
    ],
    "Meat & Seafood": [
        "BEEF", "PORK", "CHICKEN", "LAMB", "TURKEY", "SALMON", "TUNA", "SHRIMP", "LOBSTER", 
        "CRAB", "SEAFOOD", "BACON", "SAUSAGE", "STEAK", "CHICKEN BREAST", "CHICKEN WINGS"
    ],
    "Produce": [
        "FRUIT", "VEGETABLE", "LEAFY GREENS", "AVOCADO", "CABBAGE", "CARROTS", "BROCCOLI", 
        "CABBAGE", "CORN", "PEAS", "CUCUMBER", "PEPPER", "POTATOES", "ONION"
    ],
    "Pharmacy": [
        "PILLS", "MEDICINE", "VITAMINS", "SUPPLEMENTS", "COLD MEDICINE", "PAIN RELIEVER", 
        "ANTIBIOTICS", "FIRST AID", "BANDAGES", "PRESCRIPTION", "TOOTHPASTE", "SHAMPOO", "SOAP"
    ],
    "Personal Care": [
        "SHAMPOO", "TOOTHPASTE", "SOAP", "DEODORANT", "LOTIONS", "HAIR CARE", "SKIN CARE", 
        "MOISTURIZER", "MAKEUP", "NAIL POLISH", "HAIR COLOR", "FEMININE PRODUCTS", "RAZORS"
    ],
    "Pet Supplies": [
        "PET FOOD", "CAT FOOD", "DOG FOOD", "PET TOYS", "PET CARE", "LITTER", "PET SUPPLIES", 
        "PET BED", "PET COLLAR", "PET MEDICINE"
    ],
    "Electronics": [
        "LAPTOP", "PHONE", "TABLET", "CAMERA", "TV", "EARPHONES", "HEADPHONES", "CABLES", 
        "CHARGER", "SMARTWATCH", "MONITOR", "SPEAKERS", "KEYBOARD", "MOUSE", "BATTERIES"
    ],
    "Health & Fitness": [
        "EXERCISE EQUIPMENT", "DUMBBELLS", "YOGA MAT", "TREADMILL", "SUPPLEMENTS", "WEIGHT SCALE", 
        "FITNESS TRACKER", "BICYCLE", "FOOT MASSAGER", "ELASTIC BAND", "RESISTANCE BAND"
    ],
    "Office Supplies": [
        "PAPER", "PENS", "PENCILS", "NOTEBOOK", "ENVELOPES", "STAPLER", "STAPLES", "PRINTER", 
        "PRINTER INK", "BINDERS", "TAPE", "MARKERS", "WHITEBOARD", "CALENDAR"
    ],
    "Baby & Kids": [
        "DIAPERS", "BABY FOOD", "BABY WIPES", "BABY CLOTHES", "TOYS", "BABY FORMULA", "STROLLER",
        "BABY CREAM", "BABY LOTION", "KIDS CLOTHES", "KIDS TOYS", "BABY SHAMPOO"
    ],
    "Auto Supplies": [
        "OIL", "CAR BATTERY", "TIRES", "CAR WASH", "WAX", "JACK", "AIR FRESHENER", "FLOOR MATS", 
        "CAR REPAIR TOOLS", "WINDSHIELD WIPERS"
    ]
}

    lines = text.strip().split('\n')  # Split the text into lines
    product_list = []  # To store product details

    # Iterate over lines to extract product names and prices
    for line in lines:
        words = line.split()
        
        # Look for product-like lines (usually they have a name followed by a price)
        for i, word in enumerate(words):
            if word.replace('.', '', 1).isdigit():  # A number (price) is found
                price = float(word.replace('$', '').replace(',', ''))  # Clean the price
                product_name = ' '.join(words[:i])  # The product name is before the price
                
                # Classify product
                product_category = "Others"  # Default category
                for category, keywords in categories.items():
                    if any(keyword in product_name.upper() for keyword in keywords):
                        product_category = category
                        break

                # Append to product list
                product_list.append({
                    "name": product_name,
                    "price": price,
                    "category": product_category
                })

    return product_list


def extract_final_amount_from_total(text):
    """
    Extracts the final amount from the bill by searching for keywords like 'TOTAL'.
    """
    lines = text.strip().split('\n')  # Split the text into lines
    total_keywords = ["AMOUNT DUE", "BALANCE DUE", "PAYMENT", "FINAL AMOUNT", "TOTAL", "DEBIT"]

    # Iterate through the lines in reverse order (from bottom to top)
    for line in lines[::-1]:
        line_upper = line.upper()

        if any(keyword in line_upper for keyword in total_keywords):
            words = line.split()
            for word in words:
                if '$' in word:
                    final_amount = float(word.replace('$', '').replace(',', ''))
                    return final_amount
    return None


# Example OCR bill text
ocr_text = """
The Shop Chicago, IL Store #100
Large Eggs SEEEEESESSES 12.4
Cottage Cheese 6.6
Milk Natura1 yogurt 1.3
Cherry Tomatoes 11b 18.3
Bananas 11b 16.1
Cheese Crackers 11.4
wubergin Canned Tuna 12pk 20
Chocolate Cookies 8.1
Chicken breasts 30
baby wipes 2.5
Toilet Paper 1.59
TOTAL $25.97
"""

# Extract and classify products
classified_products = extract_and_classify_products(ocr_text)

# Print classified products
for product in classified_products:
    print(f"Product: {product['name']}, Price: ₹{product['price']}, Category: {product['category']}")

# Extract the final amount from the bill
final_amount = extract_final_amount_from_total(ocr_text)

# Display the final amount
if final_amount is not None:
    print(f"Final Amount: ₹{final_amount}")
else:
    print("Final amount not found.")
