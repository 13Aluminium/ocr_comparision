import os
import cv2
import numpy as np
import json
import re
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import pdf2image

# Initialize the DocTR model
# Using the default model
model = ocr_predictor(pretrained=True)

def extract_text_from_image(image_path):
    """Extract text from an image using DocTR"""
    try:
        # Load document using DocTR's DocumentFile
        doc = DocumentFile.from_images(image_path)
        
        # Run the OCR prediction
        result = model(doc)
        
        # Extract text using DocTR's built-in method
        json_output = result.export()
        
        # Extract text from the JSON output
        extracted_text = []
        
        for page in json_output['pages']:
            for block in page['blocks']:
                for line in block['lines']:
                    for word in line['words']:
                        extracted_text.append(word['value'])
                    extracted_text.append('\n')  # Add newline after each line
        
        return " ".join(extracted_text)
    except Exception as e:
        return f"Error processing image with DocTR: {str(e)}"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF using DocTR"""
    try:
        # Load document using DocTR's DocumentFile
        doc = DocumentFile.from_pdf(pdf_path)
        
        # Run the OCR prediction
        result = model(doc)
        
        # Extract text using DocTR's built-in method
        json_output = result.export()
        
        # Extract text from the JSON output
        all_text = []
        
        for page_idx, page in enumerate(json_output['pages']):
            page_text = []
            for block in page['blocks']:
                for line in block['lines']:
                    line_text = []
                    for word in line['words']:
                        line_text.append(word['value'])
                    page_text.append(" ".join(line_text))
            
            all_text.append(f"--- Page {page_idx+1} ---\n{' '.join(page_text)}")
        
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error processing PDF with DocTR: {str(e)}"

def recognize_handwriting(image_path):
    """Recognize handwritten text from an image using DocTR"""
    try:
        # Load image
        img = cv2.imread(image_path)
        
        # Apply preprocessing for handwriting
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Save the preprocessed image temporarily
        temp_path = "temp_handwriting.png"
        cv2.imwrite(temp_path, binary)
        
        # Process with DocTR
        doc = DocumentFile.from_images(temp_path)
        result = model(doc)
        
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Extract text
        json_output = result.export()
        
        extracted_text = []
        
        for page in json_output['pages']:
            for block in page['blocks']:
                for line in block['lines']:
                    line_text = []
                    for word in line['words']:
                        line_text.append(word['value'])
                    extracted_text.append(" ".join(line_text))
        
        return "\n".join(extracted_text)
    except Exception as e:
        return f"Error recognizing handwriting with DocTR: {str(e)}"

def extract_invoice_data(image_path):
    """Extract structured data from an invoice image using DocTR"""
    try:
        # Load document
        doc = DocumentFile.from_images(image_path)
        
        # Run the OCR prediction
        result = model(doc)
        
        # Extract text using DocTR's built-in method
        json_output = result.export()
        
        # Extract all text
        text_lines = []
        
        for page in json_output['pages']:
            for block in page['blocks']:
                for line in block['lines']:
                    line_text = []
                    for word in line['words']:
                        line_text.append(word['value'])
                    text_lines.append(" ".join(line_text))
        
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
        
        # Look for potential items in the invoice
        # This is a simplified approach - a real implementation would be more complex
        for line in text_lines:
            if re.search(r'\d+\.\d{2}', line):  # Look for price-like patterns
                invoice_data['items'].append(line)
        
        return json.dumps(invoice_data, indent=2)
    except Exception as e:
        return f"Error extracting invoice data with DocTR: {str(e)}"

if __name__ == "__main__":
    # If this script is run directly, allow command line testing
    import argparse
    
    parser = argparse.ArgumentParser(description='DocTR OCR Module')
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