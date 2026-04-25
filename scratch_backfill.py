import pymongo
import re

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["vaaniverify"]

orders = db.orders.find({"status": "Confirmed"})

for order in orders:
    details = order.get("order_details", "")
    
    # Try to extract a total price from order details if possible
    # e.g. "(₹24999)"
    amounts = re.findall(r'₹(\d+(?:\.\d+)?)', details)
    total_amount = float(amounts[-1]) if amounts else 2999.0
    
    # Try to extract category
    categories = []
    if "Noise-Cancelling" in details or "Headphone" in details or "Earbuds" in details or "Watch" in details:
        categories.append("electronics")
    elif "Cooker" in details or "Air Fryer" in details or "Mixer" in details:
        categories.append("kitchen")
    elif "Resistance Bands" in details or "Yoga" in details or "Football" in details:
        categories.append("sports")
    elif "Shoes" in details or "Kurta" in details or "Sunglasses" in details:
        categories.append("fashion")
    else:
        categories.append("electronics") # default
        
    db.orders.update_one(
        {"_id": order["_id"]},
        {"$set": {
            "total_amount": total_amount,
            "categories": categories
        }}
    )

print("Successfully backfilled total_amount and categories for existing confirmed orders!")
