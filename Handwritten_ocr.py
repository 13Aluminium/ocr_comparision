import cv2
import pytesseract
from pytesseract import Output
import os # For path joining

# --- Configuration ---

# !! IMPORTANT: Set this to your Tesseract installation path if it's not in your system's PATH !!
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Example for Linux/macOS (usually not needed if installed via package manager):
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract' # Or '/usr/bin/tesseract'

# Replace 'path/to/your/poem_image.png' with the actual path to your image file
image_path = '/Users/aluminium/Documents/0_CODES/1_PROJECTS/ocr_comparison_app/handwritten.jpg' # <<< CHANGE THIS TO YOUR IMAGE FILE PATH

# Confidence threshold - don't draw boxes for words below this confidence level
CONFIDENCE_THRESHOLD = 40 # Adjust as needed (0-100)

# --- Check if image exists ---
if not os.path.exists(image_path):
    print(f"Error: Image file not found at '{image_path}'")
    exit()

# --- Load the image using OpenCV ---
try:
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image file '{image_path}'. Check the file format and path.")
        exit()
    # Make a copy for drawing bounding boxes
    image_with_boxes = image.copy()
    # Convert image to grayscale (often improves OCR accuracy)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
except Exception as e:
    print(f"Error loading or processing image: {e}")
    exit()


# --- Perform OCR to get text and bounding box data ---
try:
    # Use image_to_data to get detailed information including bounding boxes
    # Use config for better page segmentation mode if needed (e.g., --psm 6 for assuming a single uniform block of text)
    # Increase DPI if needed for clearer text: config='--psm 6 --dpi 300'
    ocr_data = pytesseract.image_to_data(gray_image, output_type=Output.DICT, config='--psm 6')

    # --- Draw bounding boxes around individual words ---
    n_boxes = len(ocr_data['level'])
    print(f"Detected {n_boxes} elements. Processing word boxes (level 5)...")
    words_drawn = 0

    for i in range(n_boxes):
        # Level 5 corresponds to word-level boxes
        if ocr_data['level'][i] == 5:
            confidence = int(ocr_data['conf'][i])
            # Check if confidence is above the threshold
            if confidence > CONFIDENCE_THRESHOLD:
                (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
                word_text = ocr_data['text'][i]

                # Ensure the word text is not empty or just whitespace
                if word_text and not word_text.isspace():
                    # Draw the rectangle for this word (blue color, thickness 1)
                    cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (255, 0, 0), 1)
                    words_drawn += 1
                    # Optional: Print info about the word being boxed
                    # print(f"  Boxed word: '{word_text}' (Conf: {confidence}%) at ({x},{y},{w},{h})")


    if words_drawn == 0:
        print(f"No words detected with confidence above {CONFIDENCE_THRESHOLD} to draw boxes.")
    else:
        print(f"Drew boxes around {words_drawn} words.")


    # --- Extract the full text using image_to_string (still useful for clean text output) ---
    extracted_text = pytesseract.image_to_string(gray_image, config='--psm 6')

except pytesseract.TesseractNotFoundError:
    print("\n-------------------- TESSERACT NOT FOUND ERROR --------------------")
    # (Error message details same as before)
    print("--------------------------------------------------------------------")
    exit()
except Exception as e:
    print(f"An error occurred during OCR: {e}")
    exit()


# --- Print the extracted text ---
print("\n--- Extracted Text ---")
# Clean up potential extra newlines from OCR
clean_text = "\n".join([line for line in extracted_text.splitlines() if line.strip()])
print(clean_text)
print("----------------------")

# --- Display the image with the bounding boxes ---
cv2.imshow('Image with Word Bounding Boxes', image_with_boxes)
print("\nPress any key while the image window is active to close it.")
cv2.waitKey(0) # Wait indefinitely until a key is pressed
cv2.destroyAllWindows() # Close the image window