# main.py
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Union, Optional
from dotenv import load_dotenv
import asyncio
import json
# import re # Removed - Not needed for this simple parsing
import traceback

# --- Configuration & Initialization ---
load_dotenv()

app = FastAPI(
    title="Financial Tools API",
    description="API for analyzing finances, parsing bills (Rightmost Number + Calculated Total), and providing insights.",
    version="1.5.6", # Bumped version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Warning: GOOGLE_API_KEY not found. Endpoints using Generative AI will fail.")
else:
    try:
        genai.configure(api_key=api_key)
        print("Google Generative AI configured successfully.")
    except Exception as e:
        print(f"Error configuring Google Generative AI: {e}")
        api_key = None

# --- Pydantic Models ---
# Ensure all class definitions start at column 0
class FinancialDataInput(BaseModel):
    income: float = Field(..., gt=0, description="Monthly income")
    expenses: Dict[str, float] = Field(..., description="Dictionary of expense categories and amounts")
    savings_goals: Dict[str, float] = Field(..., description="Dictionary of saving goals and target amounts")
    discretionary_percentage: Optional[float] = Field(0.2, ge=0, le=1, description="Optional discretionary %")

class FinancialAnalysisResponse(BaseModel):
    analysis: str

class BillText(BaseModel):
    text: str = Field(..., description="The raw text extracted from the bill")

class ProductItem(BaseModel):
    name: str
    price: float
    category: str

class ParsedBillResponse(BaseModel):
    classified_products: List[ProductItem]
    final_amount: Union[float, None] = None # This will now be the calculated sum

# Removed ProductQuery model

class GeneratedInsightsResponse(BaseModel):
    insights: Union[Dict[str, Any], str]

class BillContentAnalysisResponse(BaseModel):
    analysis: str

# --- Financial Analysis Logic ---
# Ensure function definition starts at column 0
async def get_financial_analysis(data: FinancialDataInput) -> str:
    # Ensure code inside function is indented by 4 spaces
    if not api_key:
        raise HTTPException(status_code=503, detail="Google API Key not configured on server.")
    try:
        fixed_expenses = sum(data.expenses.values())
        disc_perc = data.discretionary_percentage if data.discretionary_percentage is not None else 0.2
        disc_exp = fixed_expenses * disc_perc
        prompt = f"""Analyze ... Income: ${data.income:,.2f} ... Fixed Exp: ${fixed_expenses:,.2f} ... Disc Exp: ${disc_exp:,.2f} ... Goals: {data.savings_goals} ... Provide concise analysis: 1. Timeline 2. Budget Tips 3. Investment Intro 4. Mindful Spending.""" # Truncated prompt
        print("--- Sending prompt to Gemini for /analyze-finances ---")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await asyncio.wait_for(model.generate_content_async(prompt), timeout=30.0)
        print("--- Received response from Gemini for /analyze-finances ---")
        return response.text
    except asyncio.TimeoutError:
        print("Error: Timeout GenAI (/analyze-finances).")
        raise HTTPException(status_code=504, detail="Timeout generating analysis.")
    except Exception as e:
        print(f"Error GenAI call (/analyze-finances): {e}")
        raise HTTPException(status_code=500, detail=f"Failed analysis: {e}")

# --- Bill Parsing Logic (Original "Rightmost Number" Heuristic) ---
# Ensure global variables start at column 0
PRODUCT_CATEGORIES = { # --- ENSURE COMPLETE LIST ---
    "Food": ["BREAD", "EGGS", "COTTAGE CHEESE", "YOGURT", "TOMATOES", "BANANAS", "CHICKEN", "TUNA", "VEGETABLES", "FRUIT", "POTATOES", "CARROTS", "LETTUCE", "PUMPKIN", "CABBAGE", "ONIONS", "GARLIC", "PEAS", "APPLE", "ORANGE", "PEACH", "STRAWBERRY", "GROCERIES"],
    "Beverages": ["MILK", "COFFEE", "JUICE", "WATER", "TEA", "SODA", "ENERGY DRINK", "SPORTS DRINK", "ALCOHOL", "WINE", "BEER", "COCKTAIL", "CIDER"],
    "Household": ["TOILET PAPER", "WIPES", "CLEANER", "PAPER TOWELS", "SPONGE", "MOP", "GLOVES", "DISINFECTANT", "DISH SOAP", "LAUNDRY DETERGENT", "BROOM", "TRASH BAGS", "FABRIC SOFTENER", "AIR FRESHENER", "TISSUES", "PLASTIC WRAP", "ALUMINUM FOIL", "LIGHT BULB"],
    "Snacks": ["CRACKERS", "COOKIES", "CHOCOLATE", "CANDY", "CANDY BAR", "CHIPS", "NUTS", "SEEDS", "CORN SNACKS", "TRAIL MIX", "PRETZELS", "POP CORN", "GUM", "JELLY BEANS", "GUMMY BEARS", "ICE CREAM"],
    "Dairy": ["CHEESE", "BUTTER", "MILK", "YOGURT", "CREAM", "COTTAGE CHEESE", "WHIPPED CREAM", "SOUR CREAM", "EGGS"],
    "Frozen": ["FROZEN FOOD", "FROZEN PIZZA", "FROZEN VEGETABLES", "FROZEN FRUITS", "FROZEN MEALS", "FROZEN DINNER", "FROZEN FRENCH FRIES", "FROZEN BURGERS", "FROZEN CHICKEN"],
    "Bakery": ["BREAD", "BAGELS", "CROISSANT", "MUFFINS", "DONUTS", "PASTRY", "CAKE", "PIE", "BISCUIT", "CUPCAKES", "COOKIES", "TARTS"],
    "Meat & Seafood": ["BEEF", "PORK", "CHICKEN", "LAMB", "TURKEY", "SALMON", "TUNA", "SHRIMP", "LOBSTER", "CRAB", "SEAFOOD", "BACON", "SAUSAGE", "STEAK", "CHICKEN BREAST", "CHICKEN WINGS", "FISH"],
    "Produce": ["FRUIT", "VEGETABLE", "LEAFY GREENS", "AVOCADO", "CABBAGE", "CARROTS", "BROCCOLI", "CORN", "PEAS", "CUCUMBER", "PEPPER", "POTATOES", "ONION", "MUSHROOM", "SPINACH"],
    "Pharmacy": ["PILLS", "MEDICINE", "VITAMINS", "SUPPLEMENTS", "COLD MEDICINE", "PAIN RELIEVER", "ANTIBIOTICS", "FIRST AID", "BANDAGES", "PRESCRIPTION"],
    "Personal Care": ["SHAMPOO", "TOOTHPASTE", "SOAP", "DEODORANT", "LOTIONS", "HAIR CARE", "SKIN CARE", "MOISTURIZER", "MAKEUP", "NAIL POLISH", "HAIR COLOR", "FEMININE PRODUCTS", "RAZORS", "SUNSCREEN", "CONDITIONER"],
    "Pet Supplies": ["PET FOOD", "CAT FOOD", "DOG FOOD", "PET TOYS", "PET CARE", "LITTER", "PET SUPPLIES", "PET BED", "PET COLLAR", "PET MEDICINE"],
    "Electronics": ["LAPTOP", "PHONE", "TABLET", "CAMERA", "TV", "EARPHONES", "HEADPHONES", "CABLES", "CHARGER", "SMARTWATCH", "MONITOR", "SPEAKERS", "KEYBOARD", "MOUSE", "BATTERIES"],
    "Health & Fitness": ["EXERCISE EQUIPMENT", "DUMBBELLS", "YOGA MAT", "TREADMILL", "SUPPLEMENTS", "WEIGHT SCALE", "FITNESS TRACKER", "BICYCLE", "FOOT MASSAGER", "ELASTIC BAND", "RESISTANCE BAND", "PROTEIN"],
    "Office Supplies": ["PAPER", "PENS", "PENCILS", "NOTEBOOK", "ENVELOPES", "STAPLER", "STAPLES", "PRINTER", "PRINTER INK", "BINDERS", "TAPE", "MARKERS", "WHITEBOARD", "CALENDAR"],
    "Baby & Kids": ["DIAPERS", "BABY FOOD", "BABY WIPES", "BABY CLOTHES", "TOYS", "BABY FORMULA", "STROLLER", "BABY CREAM", "BABY LOTION", "KIDS CLOTHES", "KIDS TOYS", "BABY SHAMPOO"],
    "Auto Supplies": ["OIL", "CAR BATTERY", "TIRES", "CAR WASH", "WAX", "JACK", "AIR FRESHENER", "FLOOR MATS", "CAR REPAIR TOOLS", "WINDSHIELD WIPERS", "GAS", "FUEL"],
    "Others": []
}

# --- REVERTED Extraction Functions ---
def extract_and_classify_products(text: str) -> List[ProductItem]:
    """
    Extracts products and prices by assuming the RIGHTMOST number on a line is the price.
    Classifies products based on keywords. (REVERTED LOGIC)
    """
    lines = text.strip().split('\n')
    product_list = []
    print("--- Starting Product Extraction (Rightmost Number Logic) ---")
    # Ensure loop body is indented correctly (4 spaces)
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        # print(f"Processing line {idx+1}: '{line}'") # Verbose log
        words = line.split()
        price_found: Optional[float] = None
        price_index: int = -1
        product_name: str = ""

        # Find the index of the rightmost word that looks like a number
        # Ensure loop body is indented correctly (8 spaces)
        for i in range(len(words) - 1, -1, -1):
            word = words[i]
            # Basic check: remove common non-numeric chars and see if it's potentially a float
            cleaned_word = word.replace('$', '').replace('€', '').replace('£', '').replace('₹', '').replace(',', '').replace('-', '')
            if cleaned_word and cleaned_word != '.': # Must not be empty or just a dot
                # Ensure try block is indented correctly (12 spaces)
                try:
                    # Try converting the cleaned word
                    price_found = float(cleaned_word)
                    price_index = i # Store index of the word we assume is price
                    break # Found the rightmost potential number, stop searching this line
                except ValueError:
                    continue # Word wasn't a valid number, keep searching backwards

        # Process if a price was found and there's something before it
        # Ensure 'if' block is indented correctly (8 spaces)
        if price_found is not None and price_index >= 0:
            # Name is everything *before* the identified price word index
            product_name = ' '.join(words[:price_index]).strip()

            # If name is empty (price was first word), or if name is just another number, skip
            if not product_name or product_name.isdigit():
                print(f"  Skipping line: No valid product name found before price '{price_found}'. Line: '{line}'")
                continue # Use continue instead of break inside the outer loop

            # Classify product
            product_category = "Others"
            product_name_upper = product_name.upper()
            classified = False
            # Ensure loop body is indented correctly (12 spaces)
            for category, keywords in PRODUCT_CATEGORIES.items():
                # Ensure 'if' block is indented correctly (16 spaces)
                if category == "Others":
                    continue
                # Ensure 'if' block is indented correctly (16 spaces)
                if any(f" {keyword} " in f" {product_name_upper} " or \
                       product_name_upper.endswith(f" {keyword}") or \
                       product_name_upper.startswith(f"{keyword} ") or \
                       product_name_upper == keyword for keyword in keywords):
                    product_category = category
                    classified = True
                    break # Ensure break is indented under the if
            # print(f"  Added Product: Name='{product_name}', Price={price_found}, Category='{product_category}'") # Verbose log
            product_list.append(ProductItem(name=product_name, price=price_found, category=product_category))
        # Ensure 'elif' aligns with 'if' above it (or use 'else')
        # elif line: print(f"  No reliable product/price found on line.") # Verbose log

    print(f"--- Finished Product Extraction: Found {len(product_list)} items ---")
    return product_list

# --- Function extract_final_amount_from_total REMOVED ---

# --- Helper Function for Bill Content Analysis ---
# Ensure function definition starts at column 0
async def get_bill_content_analysis(products: List[ProductItem], calculated_total: Optional[float]) -> str:
    # Modified to ONLY accept calculated_total (sum of items)
    """Generates insights specifically about the content of a parsed bill using Gemini."""
    # Ensure code inside function is indented correctly
    if not api_key:
        raise HTTPException(status_code=503, detail="Google API Key not configured on server.")
    # Check depends only on products now
    if not products:
        return "Could not extract any products from the bill to analyze."

    prompt_data = "Parsed Bill Content:\n"
    category_totals: Dict[str, float] = {}
    # Ensure 'if' block is indented correctly
    if products: # This will always be true if we reach here now
        prompt_data += "Items:\n"
        # Ensure loop body is indented correctly
        for item in products:
            # Use Rupee symbol for display clarity in prompt, assuming prices are Rupees
            prompt_data += f"- {item.name} ({item.category}): ₹{item.price:,.2f}\n"
            category_totals[item.category] = category_totals.get(item.category, 0) + item.price

    # Use the calculated total passed to the function
    # Ensure 'if' block is indented correctly
    if calculated_total is not None:
        prompt_data += f"\nCalculated Total (Sum of items): ₹{calculated_total:,.2f}\n"
    else: # Should not happen if products were found, but handle defensively
        prompt_data += "\nCalculated Total: N/A (No items found)\n"
    # Ensure 'if' block is indented correctly
    if category_totals:
        prompt_data += "\nSpending by Category (from identified items):\n"
        # Ensure loop body is indented correctly
        for category, cat_total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
            prompt_data += f"- {category}: ₹{cat_total:,.2f}\n"

    # Updated prompt to reflect using calculated total
    prompt = f"""
    Analyze the following parsed content from a single shopping bill:
    {prompt_data}
    Provide concise insights about THIS SPECIFIC BILL'S spending pattern:
    1.  **Spending Summary:** Briefly summarize the calculated total amount (around ₹{calculated_total:,.2f}) and the number of items identified.
    2.  **Category Focus:** Identify the top 1-2 spending categories *based on the items listed*.
    3.  **Item Analysis:** Comment on the types of items purchased (e.g., mostly groceries, mix of snacks and household, etc.). Are there any particularly high-cost items relative to others on this bill?
    4.  **Actionable Tip (General):** Offer ONE general money-saving tip relevant to the *types* of items found on this bill (e.g., if lots of snacks, suggest checking unit prices; if mostly groceries, suggest meal planning).
    Keep analysis focused ONLY on the data provided from this single bill. Do not assume monthly income or compare to external budgets. Be brief.
    """
    # Ensure try block is indented correctly
    try:
        print("--- Sending prompt to Gemini for /analyze_bill_content ---")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await asyncio.wait_for(model.generate_content_async(prompt), timeout=30.0)
        print("--- Received response from Gemini for /analyze_bill_content ---")
        return response.text
    # Ensure except blocks align with try
    except asyncio.TimeoutError:
        print("Error: Timeout GenAI (/analyze_bill_content).")
        return "Error: Timed out while generating insights for this bill."
    except Exception as e:
        print(f"Error during GenAI call (/analyze_bill_content): {e}")
        return f"Error: Failed to generate insights for this bill ({e})."

# --- API Endpoints ---
# Ensure decorators and functions start at column 0
@app.post("/analyze-finances", response_model=FinancialAnalysisResponse, tags=["Analysis"])
async def analyze_finances_endpoint(data: FinancialDataInput):
    """Accepts overall financial data, returns AI analysis."""
    # Ensure code inside function is indented correctly
    print(f"Received request for /analyze-finances with income: {data.income}")
    analysis_text = await get_financial_analysis(data)
    print(f"Successfully generated analysis for income: {data.income}")
    return FinancialAnalysisResponse(analysis=analysis_text)

@app.post("/parse-bill", response_model=ParsedBillResponse, tags=["Parsing"])
async def parse_bill_endpoint(bill_data: BillText):
    """
    Accepts bill text, parses products using rightmost number logic,
    and CALCULATES the final_amount by summing extracted product prices.
    """
    # Ensure code inside function is indented correctly
    print(f"Received request for /parse-bill with text length: {len(bill_data.text)}")
    if not bill_data.text or bill_data.text.isspace():
         raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    # Ensure 'try' block is indented correctly
    try:
        # Step 1: Extract products using the simple logic
        classified_products = extract_and_classify_products(bill_data.text)

        # --- Step 2: Calculate final_amount by summing prices ---
        calculated_total: Optional[float] = None
        if classified_products: # Only calculate if products were found
            total_sum = sum(item.price for item in classified_products if isinstance(item.price, (int, float))) # Add type check
            calculated_total = round(total_sum, 2) # Round to 2 decimal places
        # --- End Calculation ---

        # --- Print Results ---
        print("\n--- /parse-bill Results (Sum Calculation) ---")
        print(f"Final Amount Calculated (Sum of prices): {calculated_total if calculated_total is not None else 'N/A (No products found)'}") # Updated Log
        print(f"Products Extracted ({len(classified_products)}):")
        if classified_products:
            for item in classified_products:
                print(f"  - Name: {item.name}, Price: {item.price}, Category: {item.category}")
        else:
            print("  (No products meeting criteria found)")
        print("--- End /parse-bill Results ---\n")
        # --- END PRINTING ---

        if not classified_products: # Simplified warning
            print("Warning: Could not extract any products.")

        # Return the products and the *calculated* total
        return ParsedBillResponse(
             classified_products=classified_products,
             final_amount=calculated_total # Return the sum here
        )
    # Ensure 'except' block is indented correctly
    except Exception as e:
        print(f"Error parsing bill text. Input: '{bill_data.text[:100]}...', Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error parsing bill.")

# --- Product Recommender Endpoint REMOVED ---

@app.post("/generate_insights/", response_model=GeneratedInsightsResponse, tags=["Insights"])
async def generate_insights_endpoint():
    """Generates financial insights based on hardcoded data using Gemini."""
    # Ensure code inside function is indented correctly
    print("Received request for /generate_insights/")
    if not api_key:
        raise HTTPException(status_code=503, detail="Google API Key not configured on server.")
    expense_data_for_insights = """Product: Cottage Cheese, Price: ₹6.6, Category: Food\n...""" # Truncated
    prompt = f"""Analyze ... strictly in JSON format ... Expense Data:\n{expense_data_for_insights}\n...""" # Truncated
    try:
        print("--- Sending prompt to Gemini for /generate_insights/ ---")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print("--- Received response from Gemini for /generate_insights/ ---")
        try:
            cleaned_text = response.text.strip().strip('```json').strip('```').strip()
            insights_json = json.loads(cleaned_text)
            print("Successfully parsed Gemini response as JSON.")
            return GeneratedInsightsResponse(insights=insights_json)
        except Exception as parse_e:
            print(f"Error processing Gemini response for insights: {parse_e}. Raw: {response.text}")
            return GeneratedInsightsResponse(insights=f"Error processing AI response. Raw text: {response.text}")
    except Exception as e:
        print(f"Error during GenAI call (/generate_insights/): {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {e}")

@app.post("/analyze_bill_content", response_model=BillContentAnalysisResponse, tags=["Analysis"])
async def analyze_bill_content_endpoint(bill_data: BillText):
    """Parses input bill text (rightmost number), calculates total, and sends parsed data to Gemini for specific insights."""
    # Ensure code inside function is indented correctly
    print(f"Received request for /analyze_bill_content with text length: {len(bill_data.text)}")
    if not bill_data.text or bill_data.text.isspace():
         raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    # Ensure try block is correctly indented
    try:
        # Calls the REVERTED extraction function
        classified_products = extract_and_classify_products(bill_data.text)
        # Calculate the total based on extracted products for analysis
        final_amount_calculated: Optional[float] = None
        if classified_products:
            total_sum = sum(item.price for item in classified_products if isinstance(item.price, (int, float)))
            final_amount_calculated = round(total_sum, 2)
        # REMOVED call to extract_final_amount_from_total
        print(f"Intermediate parsing for analysis: Found {len(classified_products)} items, Calculated Total: {final_amount_calculated}")
    except Exception as e:
        print(f"Error during initial parsing step for bill analysis: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to parse bill text before analysis.")
    # Ensure second try block is indented correctly
    try:
        # Pass the CALCULATED total only to the analysis helper
        analysis_text = await get_bill_content_analysis(classified_products, final_amount_calculated)
        print("Successfully generated bill content analysis.")
        return BillContentAnalysisResponse(analysis=analysis_text)
    except HTTPException as e:
        raise e # Re-raise specific HTTP errors
    except Exception as e:
        print(f"Unexpected error calling get_bill_content_analysis: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate analysis for the parsed bill content.")

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint for basic API check."""
    # Ensure code inside function is indented correctly
    return {"message": "Welcome to the Financial Tools API. See /docs for interactive documentation."}

# To run: uvicorn main:app --host 0.0.0.0 --port 8001 --reload # USE CORRECT PORT