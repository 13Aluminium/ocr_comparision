import os
import cv2
import pytesseract
import numpy as np
from PIL import Image
import pdf2image
import re
import json

# Set the path to tesseract executable if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def _ocr_with_boxes(img, min_conf=50, custom_config=r'--oem 3 --psm 6', return_boxes=False):
    """
    Run Tesseract's image_to_data to get word boxes and assemble lines.
    If return_boxes is True, returns list of boxes (x, y, w, h, text).
    Otherwise returns the assembled text string.
    """
    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
    n = len(data['level'])
    boxes = []
    for i in range(n):
        conf = int(data['conf'][i])
        txt = data['text'][i].strip()
        if conf > min_conf and txt:
            x, y, w, h = (
                data['left'][i], data['top'][i],
                data['width'][i], data['height'][i]
            )
            boxes.append((x, y, w, h, txt))
    if return_boxes:
        return boxes
    # merge into lines
    boxes_sorted = sorted(boxes, key=lambda b: (b[1], b[0]))
    lines, current_line, current_y = [], [], None
    for x, y, w, h, txt in boxes_sorted:
        if current_y is None or abs(y - current_y) < h * 0.5:
            current_line.append((x, txt))
            current_y = y
        else:
            current_line.sort(key=lambda t: t[0])
            lines.append(" ".join(t[1] for t in current_line))
            current_line, current_y = [(x, txt)], y
    if current_line:
        current_line.sort(key=lambda t: t[0])
        lines.append(" ".join(t[1] for t in current_line))
    return "\n".join(lines)


def extract_text_from_image(image_path, min_conf=50):
    """Extract text from an image using region-based OCR"""
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        text = _ocr_with_boxes(binary, min_conf=min_conf)
        return text.strip()
    except Exception as e:
        return f"Error processing image with region-based OCR: {e}"


def extract_text_from_pdf(pdf_path, min_conf=50):
    """Extract text from a PDF by converting pages to images and doing region-based OCR"""
    try:
        images = pdf2image.convert_from_path(pdf_path)
        all_text = []
        for i, page in enumerate(images):
            opencv_img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            text = _ocr_with_boxes(binary, min_conf=min_conf)
            all_text.append(f"--- Page {i+1} ---\n" + text)
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error processing PDF with region-based OCR: {e}"


def recognize_handwriting(image_path, min_conf=40):
    """Recognize handwritten text from an image with preprocessing + region-based OCR"""
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bin_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((1, 1), np.uint8)
        bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel)
        text = _ocr_with_boxes(bin_img, min_conf=min_conf, custom_config=r'--oem 3 --psm 6 -l eng')
        return text.strip()
    except Exception as e:
        return f"Error recognizing handwriting with region-based OCR: {e}"


def extract_invoice_data(image_path, min_conf=50):
    """Extract structured invoice fields using region-based OCR"""
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        text = _ocr_with_boxes(binary, min_conf=min_conf)

        invoice_data = {'invoice_number': None, 'date': None, 'total_amount': None, 'vendor': None, 'items': []}
        invoice_match = re.search(r'(?i)invoice\s*(?:#|number|num|no|no\.)\s*[:\s]?([A-Za-z0-9\-]+)', text)
        if invoice_match:
            invoice_data['invoice_number'] = invoice_match.group(1)
        date_match = re.search(r'(?i)(?:date|dated)?\s*[:\s]?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', text)
        if date_match:
            invoice_data['date'] = date_match.group(1)
        amount_match = re.search(r'(?i)(?:total|amount|sum)?\s*(?:due|:)?\s*[\$£€]?(\d+[\.,]\d{2})', text)
        if amount_match:
            invoice_data['total_amount'] = amount_match.group(1)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            invoice_data['vendor'] = lines[0]
        return json.dumps(invoice_data, indent=2)
    except Exception as e:
        return f"Error extracting invoice data with region-based OCR: {e}"


def highlight_text_regions(image_path, output_path=None, min_conf=50, custom_config=r'--oem 3 --psm 6'):
    """Highlight text blocks detected by OCR on the image and save the annotated image."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    boxes = _ocr_with_boxes(binary, min_conf=min_conf, custom_config=custom_config, return_boxes=True)
    for x, y, w, h, _ in boxes:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # always save annotated image
    out_path = output_path or f"highlighted_{os.path.basename(image_path)}"
    cv2.imwrite(out_path, img)
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Region-based OCR Module')
    parser.add_argument('file', help='Path to file')
    parser.add_argument('--type', choices=['image', 'pdf', 'handwriting', 'invoice', 'highlight'],
                        default='image', help='Type of OCR')
    parser.add_argument('--min_conf', type=int, default=50,
                        help='Minimum confidence threshold for OCR words')
    parser.add_argument('--output', help='Path to save highlighted image')
    args = parser.parse_args()

    if args.type == 'image':
        print(extract_text_from_image(args.file, min_conf=args.min_conf))
    elif args.type == 'pdf':
        print(extract_text_from_pdf(args.file, min_conf=args.min_conf))
    elif args.type == 'handwriting':
        print(recognize_handwriting(args.file, min_conf=args.min_conf))
    elif args.type == 'invoice':
        print(extract_invoice_data(args.file, min_conf=args.min_conf))
    elif args.type == 'highlight':
        # first extract and print text
        text = extract_text_from_image(args.file, min_conf=args.min_conf)
        print(text)
        # then highlight and save image
        out_path = highlight_text_regions(args.file, output_path=args.output, min_conf=args.min_conf)
        print(f"Annotated image saved to {out_path}")
