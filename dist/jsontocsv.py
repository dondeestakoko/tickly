import json
import csv
import re
from tkinter import Tk, filedialog

def ask_for_json():
    # Create a Tkinter root window and hide it
    root = Tk()
    root.withdraw()

    # Open file dialog to choose the image file
    file_path = filedialog.askopenfilename(
        title="Select a Receipt JSON File", 
        filetypes=[("Image Files", "*.json")]
    )

    # Check if a file was selected
    if file_path:
        return file_path
    else:
        print("No file selected")
        return None


def clean_and_convert(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_rows = []
    seen_rows = set()
    
    for receipt in data:
        store_name = receipt.get("store_name", "N/A")
        store_email = receipt.get("store_email", "N/A")
        store_address = receipt.get("store_address", "N/A") # Clean newlines and commas
        total_amount = receipt.get("total_amount", 0)
        tax_amount = receipt.get("tax_amount", 0)
        payment_type = receipt.get("payment_type", "N/A")
        receipt_id = receipt.get("id", "N/A")
        date_time = receipt.get("date_time", "N/A")
        ticket_number = receipt.get("ticket_number", "N/A")

        items = receipt.get("items", [])
        
        merged_items = []
        current_item = None
        
        for item in items:
            name = item.get("description", item.get("full_description", "N/A")).replace('\n', ' ').replace(",", " ")
            quantity = item.get("quantity", 1)
            price = item.get("price")
            total = item.get("total")
            item_type = item.get("type", "N/A")
            
            if current_item and price is None and total is None:
                current_item["name"] += f" {name}"
            else:
                if current_item:
                    merged_items.append(current_item)
                current_item = {
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "total": total,
                    "type": item_type
                }
        
        if current_item:
            merged_items.append(current_item)
        
        for item in merged_items:
            if item["price"] is None and item["total"] is not None:
                item["price"] = round(item["total"] / item["quantity"], 2)
            if item["total"] is None and item["price"] is not None:
                item["total"] = round(item["price"] * item["quantity"], 2)
            
            tax_base = total_amount - tax_amount if total_amount and tax_amount else "N/A"
            tax_rate = round((tax_amount / tax_base) * 100, 2) if tax_base != "N/A" and tax_base > 0 else "N/A"
            
            row = (
                store_name, store_email, store_address, total_amount, tax_amount, payment_type, receipt_id, date_time, ticket_number,
                item["name"], item["quantity"], item["price"], item["total"], item["type"],
                tax_base, tax_rate
            )
            
            if row not in seen_rows:
                seen_rows.add(row)
                cleaned_rows.append(row)
    
    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)  # Ensure proper quoting
        writer.writerow([
            "Store Name", "Store Email", "Store Address", "Total Amount", "Tax Amount", "Payment Type", "Receipt ID", "Date Time", "Ticket Number",
            "Item Name", "Quantity", "Price", "Total", "Item Type", "Tax Base", "Tax Rate (%)"
        ])
        writer.writerows(cleaned_rows)
    
    print(f"CSV file saved as {csv_file}")
