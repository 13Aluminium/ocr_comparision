import os
import cv2
import numpy as np
import easyocr
import pdf2image
import json
import re

# Initialize EasyOCR reader with English language
reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path):
    """Extract text from an image using EasyOCR"""
    try:
        # Load image
        img = cv2.imread(image_path)
        
        # Run EasyOCR
        results = reader.readtext(img)
        
        # Extract text
        extracted_text = []
        for (bbox, text, prob) in results:
            extracted_text.append(text)
        
        return "\n".join(extracted_text)
    except Exception as e:
        return f"Error processing image with EasyOCR: {str(e)}"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF using EasyOCR"""
    try:
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        all_text = []
        
        # Process each page
        for i, image in enumerate(images):
            # Convert PIL image to numpy array
            np_image = np.array(image)
            
            # Run EasyOCR
            results = reader.readtext(np_image)
            
            # Extract text
            page_text = []
            for (bbox, text, prob) in results:
                page_text.append(text)
            
            all_text.append(f"--- Page {i+1} ---\n{' '.join(page_text)}")
        
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error processing PDF with EasyOCR: {str(e)}"

def recognize_handwriting(image_path):
    """Recognize handwritten text from an image using EasyOCR"""
    try:
        # Load image
        img = cv2.imread(image_path)
        
        # Apply preprocessing for handwriting
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Run EasyOCR with enhanced image
        results = reader.readtext(enhanced)
        
        # Extract text
        extracted_text = []
        for (bbox, text, prob) in results:
            extracted_text.append(text)
        
        return "\n".join(extracted_text)
    except Exception as e:
        return f"Error recognizing handwriting with EasyOCR: {str(e)}"

def extract_invoice_data(image_path):
    """Extract structured data from an invoice image using EasyOCR"""
    try:
        # Load image
        img = cv2.imread(image_path)
        
        # Run EasyOCR
        results = reader.readtext(img)
        
        # Extract all text
        text_lines = []
        bbox_data = []
        
        for (bbox, text, prob) in results:
            text_lines.append(text)
            bbox_data.append((bbox, text))
        
        full_text = " ".join(text_lines)
        
        # Parse invoice data
        invoice_data = {
            'invoice_number': None,
            'date': None,
            'total_amount': None,
            'vendor': None,
            'items': []
        }
        
        # Extract invoice number
        invoice_match = re.search(r'(?i)invoice\s*(?:#|number|num|no|no\.)\s*[:\s]?\s*([a-zA-Z0-9\-]+)', full_text)
        if invoice_match:
            invoice_data['invoice_number'] = invoice_match.group(1)
        
        # Extract date
        date_match = re.search(r'(?i)(?:date|dated)?\s*[:\s]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', full_text)
        if date_match:
            invoice_data['date'] = date_match.group(1)
        
        # Extract total amount
        amount_match = re.search(r'(?i)(?:total|amount|sum)?\s*(?:due|:)?\s*[\$£€]?\s*(\d+[.,]\d{2})', full_text)
        if amount_match:
            invoice_data['total_amount'] = amount_match.group(1)
        
        # Try to extract vendor name (typically at the top of the invoice)
        if text_lines:
            invoice_data['vendor'] = text_lines[0]
        
        # Attempt to identify items based on layout and content
        # This is a simplified approach - real implementation would be more complex
        # Using y-coordinate sorting to find rows
        sorted_boxes = sorted(bbox_data, key=lambda x: (sum(point[1] for point in x[0]) / 4))
        
        # Look for lines that might contain prices
        for bbox, text in sorted_boxes:
            if re.search(r'\d+\.\d{2}', text):  # Look for price-like patterns
                invoice_data['items'].append(text)
        
        return json.dumps(invoice_data, indent=2)
    except Exception as e:
        return f"Error extracting invoice data with EasyOCR: {str(e)}"

if __name__ == "__main__":
    # If this script is run directly, allow command line testing
    import argparse
    
    parser = argparse.ArgumentParser(description='EasyOCR Module')
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