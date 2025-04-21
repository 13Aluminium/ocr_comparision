import os
import cv2
import pytesseract
import numpy as np
from PIL import Image
import pdf2image
import re
import json

# Set the path to tesseract executable if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Uncomment and adjust for Windows

def extract_text_from_image(image_path):
    """Extract text from an image using pytesseract"""
    try:
        # Read image using OpenCV for preprocessing
        img = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply threshold to get image with only black and white
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Use pytesseract to extract text
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(binary, config=custom_config)
        
        return text.strip()
    except Exception as e:
        return f"Error processing image with PyTesseract: {str(e)}"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF using pytesseract"""
    try:
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        all_text = []
        
        # Process each page
        for i, image in enumerate(images):
            # Convert PIL image to numpy array
            opencvImage = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            # Convert to grayscale
            gray = cv2.cvtColor(opencvImage, cv2.COLOR_BGR2GRAY)
            # Apply threshold
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Extract text
            custom_config = r'--oem 3 --psm 3'
            text = pytesseract.image_to_string(binary, config=custom_config)
            all_text.append(f"--- Page {i+1} ---\n{text}")
        
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error processing PDF with PyTesseract: {str(e)}"

def recognize_handwriting(image_path):
    """Recognize handwritten text from an image using pytesseract"""
    try:
        # Read image
        img = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing specifically for handwriting
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY_INV, 11, 2)
        # Apply morphological operations to reduce noise
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.dilate(binary, kernel, iterations=1)
        
        # Recognize text with specific configuration for handwriting
        custom_config = r'--oem 3 --psm 3 -l eng'
        text = pytesseract.image_to_string(binary, config=custom_config)
        
        return text.strip()
    except Exception as e:
        return f"Error recognizing handwriting with PyTesseract: {str(e)}"

def extract_invoice_data(image_path):
    """Extract structured data from an invoice image using pytesseract"""
    try:
        # Read image
        img = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply threshold
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Extract all text
        text = pytesseract.image_to_string(binary)
        
        # Parse invoice data
        invoice_data = {
            'invoice_number': None,
            'date': None,
            'total_amount': None,
            'vendor': None,
            'items': []
        }
        
        # Extract invoice number (common formats include "Invoice #", "Invoice Number", etc.)
        invoice_match = re.search(r'(?i)invoice\s*(?:#|number|num|no|no\.)\s*[:\s]?\s*([a-zA-Z0-9\-]+)', text)
        if invoice_match:
            invoice_data['invoice_number'] = invoice_match.group(1)
        
        # Extract date
        date_match = re.search(r'(?i)(?:date|dated)?\s*[:\s]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', text)
        if date_match:
            invoice_data['date'] = date_match.group(1)
        
        # Extract total amount
        amount_match = re.search(r'(?i)(?:total|amount|sum)?\s*(?:due|:)?\s*[\$£€]?\s*(\d+[.,]\d{2})', text)
        if amount_match:
            invoice_data['total_amount'] = amount_match.group(1)
        
        # Try to extract vendor name (often at the top of the invoice)
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        if non_empty_lines:
            invoice_data['vendor'] = non_empty_lines[0]
        
        return json.dumps(invoice_data, indent=2)
    except Exception as e:
        return f"Error extracting invoice data with PyTesseract: {str(e)}"

if __name__ == "__main__":
    # If this script is run directly, allow command line testing
    import argparse
    
    parser = argparse.ArgumentParser(description='PyTesseract OCR Module')
    parser.add_argument('file', help='Path to file')
    parser.add_argument('--type', choices=['image', 'pdf', 'handwriting', 'invoice'], 
                        default='image', help='Type of OCR to perform')
    
    args = parser.parse_args()
    
    if args.type == 'image':
        result = extract_text_from_image(args.file)
    elif args.type == 'pdf':
        result = extract_text_from_pdf(args.file)
    elif args.type == 'handwriting':
        result = recognize_handwriting(args.file)
    elif args.type == 'invoice':
        result = extract_invoice_data(args.file)
    
    print(result)