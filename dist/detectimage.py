import requests
import json
import os
from datetime import datetime
import re
import cv2
from tkinter import Tk, filedialog, Button, Label
from PIL import Image, ImageTk
from jsontocsv import clean_and_convert
import sys
import tkinter as tk

# API endpoint for uploading the receipt
url_upload = "https://api.veryfi.com/api/v8/partner/documents/"

# Capture image via webcam
def capture_image():
    cam = cv2.VideoCapture(0)  # Ouvrir la webcam
    cv2.namedWindow("Capture Receipt")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break
        cv2.imshow("Capture Receipt", frame)

        key = cv2.waitKey(1)
        if key % 256 == 32:  # Barre espace pour capturer
            img_name = "captured_receipt.jpg"
            cv2.imwrite(img_name, frame)
            print(f"Image saved as {img_name}")
            break

    cam.release()
    cv2.destroyAllWindows()
    return img_name

# Fonction pour sélectionner une image à partir de l'ordinateur
def select_image():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select a Receipt Image",
                                           filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    return file_path if file_path else None

# Interface graphique pour capturer ou choisir une image

# Proceed if an image was selected
def process_image(image_file_path):
    # Open the image file and upload it
    with open(image_file_path, 'rb') as f:
        files = {
            'file': (image_file_path, f, 'image/jpeg'),  # Explicit MIME type
        }
        headers = {
            'Accept': 'application/json',
            'CLIENT-ID': 'vrfxL460XKK4RXsn8Yp8dF2a4kVNz7SLnS9zVPY',
            'AUTHORIZATION': 'apikey lemdanikoko2:c197fd8b16e12407d36e9a72672c7c8a'
        }

        # POST request to upload the image (receipt)
        response = requests.post(url_upload, headers=headers, files=files)

        # Debugging: Print the full response from the upload request
        print("Upload Response Status Code:", response.status_code)
        print("Upload Response Body:", response.text)
        with open("response.txt", "w", encoding="utf-8") as file:
            file.write(response.text)

        print("Response saved to response.txt")

        # Check if the id is returned (instead of document_id)
        document_id = response.json().get('id')

        if document_id:
            # Step 2: Retrieve the processed data in JSON
            url_get = f"https://api.veryfi.com/api/v8/partner/documents/{document_id}"

            # GET request to retrieve the document data (processed receipt details)
            response_get = requests.get(url_get, headers=headers)

            # Directly access the JSON content without checking status
            receipt_data = response_get.json()

            # Extract OCR Text to get ticket Date and number
            ocr_text = receipt_data.get('ocr_text', '')

            # Regex to find date and time (e.g., 04/01/2025 15:27:56)
            datetime_match = re.search(r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})", ocr_text)
            ticket_datetime = None
            if datetime_match:
                datetime_str = datetime_match.group(1)
                try:
                    ticket_datetime = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    print(f"Error parsing datetime: {datetime_str}")
                    ticket_datetime = None

            formatted_date_time = ticket_datetime.strftime("%d-%m-%Y %H:%M:%S") if ticket_datetime else datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            # Extract ticket number using the new regex

            relevant_data = { 
        'id': receipt_data.get('id', 'N/A'),
        'store_name': receipt_data.get('vendor', {}).get('name', 'N/A'),
        'store_email': receipt_data.get('vendor', {}).get('email', 'N/A'),
        'store_address': receipt_data.get('vendor', {}).get('address', 'N/A'),
        'total_amount': receipt_data.get('total', 'N/A'),
        'subtotal': receipt_data.get('subtotal', 'N/A'),
        'tax_amount': receipt_data.get('tax', 'N/A'),
        'tax_rate': receipt_data.get('tax_lines', [{}])[0].get('rate', 'N/A'),  # First tax rate if available
        'currency': receipt_data.get('currency_code', 'N/A'),
        'payment_type': receipt_data.get('payment', {}).get('type', 'N/A'),
        'ticket_number': receipt_data.get('invoice_number', 'N/A'),  # Fixed the key name
        'date_time': receipt_data.get('date', 'N/A'),  # Now using the actual receipt date
        'document_type': receipt_data.get('document_type', 'N/A'),
        'document_title': receipt_data.get('document_title', 'N/A'),
        'category': receipt_data.get('category', 'N/A'),
        'country_code': receipt_data.get('country_code', 'N/A'),
        'duplicate_of': receipt_data.get('duplicate_of', 'N/A'),
        'items': [
            {
                'description': item.get('description', 'N/A'),
                'full_description': item.get('full_description', 'N/A'),
                'quantity': item.get('quantity', 'N/A'),
                'price': item.get('price', 'N/A'),
                'total': item.get('total', 'N/A')
            } for item in receipt_data.get('line_items', [])
        ],
        'image_url': receipt_data.get('img_url', 'N/A'),
        'thumbnail_url': receipt_data.get('img_thumbnail_url', 'N/A'),
        'pdf_url': receipt_data.get('pdf_url', 'N/A')
    }

            # Initialize a variable to hold the current item details in case of line breaks
            current_item = None
            # Ensure items are not duplicated
            existing_items = [item['description'] for item in relevant_data['items']]

            # Extract item details (if available) and add to the items list
            for item in receipt_data.get('line_items', []):
                # If the current item is not empty and the current item has no description,
                # it means the next line is a continuation of the same product
                if current_item and not item.get('description'):
                    # Merge item details with the previous product (current_item)
                    current_item['price'] = item.get('price', current_item['price'])
                    current_item['total'] = item.get('total', current_item['total'])
                    current_item['quantity'] += item.get('quantity', 1)  # Add quantity if available
                else:
                    # If we have a complete new item, save the old one (if exists)
                    if current_item:
                        # Check if the item already exists in the list before appending
                        if current_item['description'] not in existing_items:
                            relevant_data['items'].append(current_item)
                            existing_items.append(current_item['description'])  # Add to the list of existing items

                    # Now we can start a new item
                    current_item = {
                        'description': item.get('description', 'N/A'),
                        'quantity': item.get('quantity', 1),  # Default to 1 if quantity is not available
                        'price': item.get('price', 'N/A'),
                        'total': item.get('total', 'N/A'),
                        'type': item.get('type', 'N/A')
                    }

            # Ensure the last item is added if it's incomplete
            if current_item:
                if current_item['description'] not in existing_items:
                    relevant_data['items'].append(current_item)
                    existing_items.append(current_item['description'])  # Add to the list of existing items

            # Specify the file path for JSON
            json_file_path = 'extracted_receipt.json'

            # Check if the JSON file already exists
            if os.path.exists(json_file_path):
                # Read the existing data to append new data
                with open(json_file_path, 'r') as json_file:
                    existing_data = json.load(json_file)

                # Ensure existing_data is parsed as a list of dictionaries
                try:
                    existing_data = json.loads(existing_data) if isinstance(existing_data, str) else existing_data
                except json.JSONDecodeError:
                    print("Error decoding existing JSON data. Starting fresh.")
                    existing_data = []

                # Check if the document ID or receipt details already exist in the JSON
                is_duplicate = False
                for entry in existing_data:
                    if isinstance(entry, dict) and entry.get('id') == document_id:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    # Append the new data to the JSON file
                    existing_data.append(relevant_data)
                    with open(json_file_path, 'w') as json_file:
                        json.dump(existing_data, json_file, indent=4)

                    print(f"New receipt data added to {json_file_path}")
                else:
                    print("This receipt is a duplicate and will not be saved.")
            else:
                # If the JSON file doesn't exist, create a new one
                with open(json_file_path, 'w') as json_file:
                    json.dump([relevant_data], json_file, indent=4)
                print(f"New receipt data saved to {json_file_path}")
            clean_and_convert(json_file_path, 'receipt_data.csv')

        else:
            print("Failed to get document ID. Check if the image was uploaded successfully.")

def on_closing():
    # Perform any necessary cleanup
    print("Closing the application...")
    sys.exit()  # Exits the program

def start_gui():
    root = tk.Tk()    
    root.title("Receipt Scanner")

    label = Label(root, text="Capture or Upload Receipt", font=("Arial", 14))
    label.pack(pady=10)

    btn_capture = Button(root, text="Capture via Webcam", command=lambda: process_image(capture_image()))
    btn_capture.pack(pady=5)

    btn_select = Button(root, text="Select from Computer", command=lambda: process_image(select_image()))
    btn_select.pack(pady=5)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the close button to on_closing
    root.mainloop()

# Start the GUI
start_gui()
