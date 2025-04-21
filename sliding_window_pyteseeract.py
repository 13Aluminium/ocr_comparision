import os
import cv2
import pytesseract
import numpy as np
from PIL import Image
import pdf2image
import re
import json
from collections import defaultdict
from difflib import SequenceMatcher

def similar(a, b):
    """Calculate the similarity ratio between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def clean_word_repetitions(text):
    """Clean repeated words that appear right next to each other"""
    words = text.split()
    if not words:
        return ""
    
    cleaned_words = [words[0]]
    for i in range(1, len(words)):
        if words[i] != words[i-1]:
            cleaned_words.append(words[i])
    
    return " ".join(cleaned_words)

def save_highlighted_row(img, y, row_height, width, output_path, index):
    """Save an image with the current row highlighted"""
    # Create a copy of the image to draw on
    img_copy = img.copy()
    
    # Calculate end y coordinate ensuring we stay within image boundaries
    end_y = min(y + row_height, img.shape[0])
    
    # Define highlight color (semi-transparent green)
    overlay = img_copy.copy()
    cv2.rectangle(overlay, (0, y), (width, end_y), (0, 255, 0), -1)
    
    # Apply transparency
    alpha = 0.3  # Transparency factor
    cv2.addWeighted(overlay, alpha, img_copy, 1 - alpha, 0, img_copy)
    
    # Add border for better visibility
    cv2.rectangle(img_copy, (0, y), (width, end_y), (0, 255, 0), 2)
    
    # Add text showing the row index
    cv2.putText(img_copy, f"Row {index}", (10, y - 10 if y > 20 else y + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Save the image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img_copy)
    
    return output_path

def extract_text_with_row_sliding_window(image_path, row_height=100, overlap=20, visualize=False):
    """Extract text using a row-based sliding window approach"""
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return f"Error: Unable to read image at {image_path}"
            
        height, width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Get global text as reference
        global_text = pytesseract.image_to_string(binary, config=r'--oem 3 --psm 1')
        
        # Process the image in horizontal strips (rows)
        text_by_row = []
        
        # Create visualization directory if needed
        if visualize:
            visualization_dir = "row_visualizations"
            os.makedirs(visualization_dir, exist_ok=True)
        
        # Define how many rows to process
        step = row_height - overlap
        row_index = 0
        
        for y in range(0, height - row_height + step, step):
            # Ensure we stay within image boundaries
            end_y = min(y + row_height, height)
            
            # Extract horizontal strip
            row_img = binary[y:end_y, 0:width]
            
            # Skip empty or mostly white rows
            if np.mean(row_img) > 250:  # Skip rows that are mostly white
                continue
            
            # Visualize this row if requested
            if visualize:
                vis_path = os.path.join("row_visualizations", f"row_{row_index:03d}.jpg")
                save_highlighted_row(img, y, row_height, width, vis_path, row_index)
                row_index += 1
            
            # Process text in this row with different PSM modes
            best_text = ""
            best_score = 0
            
            psm_modes = [6, 7, 3]  # 6=Block of text, 7=Single line, 3=Auto
            
            for psm in psm_modes:
                config = f'--oem 3 --psm {psm}'
                data = pytesseract.image_to_data(row_img, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract valid text blocks (with confidence > 40)
                valid_indices = [i for i, conf in enumerate(data['conf']) if conf > 40 and data['text'][i].strip()]
                row_text = " ".join([data['text'][i] for i in valid_indices])
                
                # Calculate a score based on text length and average confidence
                if valid_indices:
                    avg_conf = sum([data['conf'][i] for i in valid_indices]) / len(valid_indices)
                    score = len(row_text) * avg_conf
                    
                    if score > best_score:
                        best_score = score
                        best_text = row_text
            
            # If we found any text in this row
            if best_text:
                # Clean any repeated words
                cleaned_text = clean_word_repetitions(best_text)
                text_by_row.append({
                    'y': y,
                    'text': cleaned_text,
                    'row_index': row_index - 1 if visualize else None  # Store reference to visualization
                })
        
        # Merge overlapping rows
        merged_rows = []
        
        i = 0
        while i < len(text_by_row):
            current_row = text_by_row[i]
            j = i + 1
            
            # Look ahead for overlapping rows
            while j < len(text_by_row) and text_by_row[j]['y'] < current_row['y'] + row_height:
                # If there's significant text overlap, merge them
                if similar(current_row['text'], text_by_row[j]['text']) > 0.5:
                    # Choose the longer text
                    if len(text_by_row[j]['text']) > len(current_row['text']):
                        current_row = text_by_row[j]
                j += 1
            
            merged_rows.append(current_row['text'])
            i = j
        
        # Combine all rows into final text
        result_text = "\n".join(merged_rows)
        
        # Fallback to global text if our processing fails or gives sparse results
        if len(result_text) < len(global_text) * 0.5:
            return global_text
        
        # If visualizing, create a composite image showing all selected rows
        if visualize and text_by_row:
            # Create composite image
            composite_path = os.path.join("row_visualizations", "all_selected_rows.jpg")
            img_copy = img.copy()
            
            for row_data in text_by_row:
                y = row_data['y']
                end_y = min(y + row_height, height)
                
                # Add semi-transparent highlight
                overlay = img_copy.copy()
                cv2.rectangle(overlay, (0, y), (width, end_y), (0, 255, 0), -1)
                cv2.addWeighted(overlay, 0.3, img_copy, 0.7, 0, img_copy)
                
                # Add border
                cv2.rectangle(img_copy, (0, y), (width, end_y), (0, 255, 0), 2)
                
                # Add row index text
                if row_data['row_index'] is not None:
                    cv2.putText(img_copy, f"Row {row_data['row_index']}", (10, y - 10 if y > 20 else y + 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imwrite(composite_path, img_copy)
            
            # Return additional info about visualization
            return {
                'text': result_text,
                'visualization_dir': visualization_dir,
                'composite_image': composite_path,
                'total_rows': row_index
            }
        
        return result_text
    except Exception as e:
        return f"Error processing image with row-based sliding window: {str(e)}"

def enhance_image_for_ocr(image_path, output_path=None):
    """Enhance image for better OCR results"""
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Denoise image
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    
    # Apply dilation to thicken the text slightly
    kernel = np.ones((1, 1), np.uint8)
    dilated = cv2.dilate(denoised, kernel, iterations=1)
    
    if output_path:
        cv2.imwrite(output_path, dilated)
        return output_path
    else:
        temp_path = "temp_enhanced.jpg"
        cv2.imwrite(temp_path, dilated)
        return temp_path

def extract_text_using_multiple_strip_heights(image_path, visualize=False):
    """Extract text using various strip heights to handle different document layouts"""
    # Try different strip heights and select the best result
    strip_heights = [50, 100, 150]
    results = []
    visualization_results = []
    
    # Get global text as reference
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    global_text = pytesseract.image_to_string(binary, config=r'--oem 3 --psm 1')
    
    # Process with different strip heights
    for height in strip_heights:
        overlap = height // 3  # 1/3 overlap
        result = extract_text_with_row_sliding_window(image_path, height, overlap, visualize)
        
        if visualize and isinstance(result, dict):
            visualization_results.append({
                'height': height,
                'visualization_dir': result['visualization_dir'],
                'composite_image': result['composite_image'],
                'text': result['text'],
                'total_rows': result['total_rows']
            })
            results.append(result['text'])
        else:
            results.append(result)
    
    # Add global text as another option
    results.append(global_text)
    
    # Choose the best result based on length and text quality
    best_result = None
    best_score = 0
    best_height = None
    
    for i, result in enumerate(results):
        # Calculate a quality score based on text length and lack of repetition
        words = result.split()
        unique_words = set(words)
        
        # Score: text length with penalty for repetition
        if len(words) > 0:
            repetition_ratio = len(unique_words) / len(words)
            score = len(result) * repetition_ratio
            
            if score > best_score:
                best_score = score
                best_result = result
                if i < len(strip_heights):
                    best_height = strip_heights[i]
                else:
                    best_height = "global"
    
    if visualize and visualization_results:
        # Find the visualization result for the best height
        best_viz = None
        for viz in visualization_results:
            if viz['height'] == best_height:
                best_viz = viz
                break
        
        if best_viz:
            return {
                'text': best_result,
                'best_height': best_height,
                'visualization': best_viz['composite_image'],
                'all_visualizations': [v['composite_image'] for v in visualization_results]
            }
    
    return best_result

def combine_rows_and_global_approaches(image_path, visualize=False):
    """Combine row-based approach with global OCR for best results"""
    # Get global text
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    global_text = pytesseract.image_to_string(binary, config=r'--oem 3 --psm 1')
    global_text = clean_word_repetitions(global_text)
    
    # Get row-based text (with multiple strip heights)
    row_text_result = extract_text_using_multiple_strip_heights(image_path, visualize)
    
    if visualize and isinstance(row_text_result, dict):
        row_text = row_text_result['text']
        visualization = row_text_result['visualization']
    else:
        row_text = row_text_result
        visualization = None
    
    # Split into lines
    global_lines = global_text.strip().split('\n')
    row_lines = row_text.strip().split('\n')
    
    # Merge lines based on similarity
    result_lines = []
    
    # Process each line from row-based text
    for row_line in row_lines:
        if not row_line.strip():
            continue
            
        best_match = None
        best_ratio = 0
        
        # Find the most similar line in global text
        for gl_line in global_lines:
            if not gl_line.strip():
                continue
                
            ratio = similar(row_line, gl_line)
            if ratio > best_ratio and ratio > 0.5:  # 0.5 similarity threshold
                best_ratio = ratio
                best_match = gl_line
        
        # Choose the better line
        if best_match:
            # Choose the longer line if they're similar enough
            if len(row_line) > len(best_match):
                result_lines.append(row_line)
            else:
                result_lines.append(best_match)
        else:
            # No good match found, include the row line
            result_lines.append(row_line)
    
    # Check if we have enough lines
    if len(result_lines) < len(global_lines) * 0.5:
        # Not enough lines, fall back to the global text
        combined_text = global_text
    else:
        # Return combined result
        combined_text = "\n".join(result_lines)
    
    if visualize and visualization:
        return {
            'text': combined_text,
            'visualization': visualization
        }
    
    return combined_text

def extract_text_from_pdf(pdf_path, use_row_based=True, visualize=False):
    """Extract text from a PDF using row-based sliding window approach"""
    try:
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        all_text = []
        all_visualizations = []
        
        # Process each page
        for i, image in enumerate(images):
            # Convert PIL image to numpy array
            opencvImage = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Save temporary image
            temp_image_path = f"temp_page_{i}.jpg"
            cv2.imwrite(temp_image_path, opencvImage)
            
            # Extract text
            if use_row_based:
                result = combine_rows_and_global_approaches(temp_image_path, visualize)
                if visualize and isinstance(result, dict):
                    text = result['text']
                    all_visualizations.append({
                        'page': i+1,
                        'visualization': result['visualization']
                    })
                else:
                    text = result
            else:
                # Use standard approach
                gray = cv2.cvtColor(opencvImage, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                text = pytesseract.image_to_string(binary, config=r'--oem 3 --psm 1')
            
            all_text.append(f"--- Page {i+1} ---\n{text}")
            
            # Remove temporary image
            os.remove(temp_image_path)
        
        combined_text = "\n\n".join(all_text)
        
        if visualize and all_visualizations:
            return {
                'text': combined_text,
                'visualizations': all_visualizations
            }
        
        return combined_text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def detect_optimal_row_height(image_path):
    """Auto-detect optimal row height based on document analysis"""
    try:
        # Read image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Run OCR with hOCR output to get line information
        hocr_data = pytesseract.image_to_data(binary, config='--oem 3 --psm 1', output_type=pytesseract.Output.DICT)
        
        # Calculate heights of detected text blocks
        heights = []
        for i in range(len(hocr_data['height'])):
            if hocr_data['conf'][i] > 30 and hocr_data['text'][i].strip():
                heights.append(hocr_data['height'][i])
        
        # If we have height data
        if heights:
            # Calculate median height and add some margin
            median_height = sorted(heights)[len(heights) // 2]
            optimal_height = int(median_height * 2.5)  # 2.5x to capture a line plus some context
            
            # Ensure height is reasonable (between 40 and 200 pixels)
            optimal_height = max(40, min(200, optimal_height))
            
            return optimal_height
        else:
            # Default if detection fails
            return 100
    except Exception:
        # Default if exception occurs
        return 100

if __name__ == "__main__":
    # If this script is run directly, allow command line testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Row-Based OCR Module')
    parser.add_argument('file', help='Path to file')
    parser.add_argument('--type', choices=['image', 'pdf'], 
                        default='image', help='Type of file to process')
    parser.add_argument('--row-height', type=int, default=None,
                        help='Height of row strips in pixels (default: auto-detect)')
    parser.add_argument('--overlap', type=int, default=None,
                        help='Overlap between rows in pixels (default: 1/3 of row height)')
    parser.add_argument('--enhance', action='store_true',
                        help='Enhance image before OCR')
    parser.add_argument('--auto', action='store_true',
                        help='Use auto-optimization for all parameters')
    parser.add_argument('--visualize', action='store_true',
                        help='Generate visualizations of rows being processed')
    
    args = parser.parse_args()
    
    # Enhance image if requested
    file_path = args.file
    if args.enhance and args.type != 'pdf':
        file_path = enhance_image_for_ocr(args.file)
    
    # Process the file according to type
    if args.type == 'image':
        if args.auto:
            # Use multiple strip heights and select best result
            result = extract_text_using_multiple_strip_heights(file_path, args.visualize)
        else:
            # Auto-detect row height if not specified
            row_height = args.row_height if args.row_height else detect_optimal_row_height(file_path)
            # Default overlap to 1/3 of row height if not specified
            overlap = args.overlap if args.overlap else row_height // 3
            
            print(f"Using row height: {row_height}, overlap: {overlap}")
            result = extract_text_with_row_sliding_window(file_path, row_height, overlap, args.visualize)
    elif args.type == 'pdf':
        result = extract_text_from_pdf(file_path, True, args.visualize)
    
    # Clean up temporary file if created
    if args.enhance and args.type != 'pdf' and file_path != args.file:
        os.remove(file_path)
    
    # Display results
    if isinstance(result, dict) and args.visualize:
        print(f"OCR text extracted and visualizations generated.")
        print(f"Visualization images can be found in: {result.get('visualization_dir', 'row_visualizations')}")
        if 'visualization' in result:
            print(f"Main visualization: {result['visualization']}")
        print("\n" + result['text'])
    else:
        print(result)