import paddleocr
import numpy as np
import cv2 # Make sure opencv is installed

try:
    print("Initializing PaddleOCR...")
    # Initialize PaddleOCR explicitly for CPU
    ocr_engine = paddleocr.PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=True)
    print("PaddleOCR initialized.")

    # Create a dummy black image
    dummy_image = np.zeros((100, 400, 3), dtype=np.uint8)
    cv2.putText(dummy_image, 'TEST', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    print("Dummy image created.")

    # Run OCR on the dummy image
    print("Running OCR...")
    result = ocr_engine.ocr(dummy_image, cls=True)
    print("OCR finished.")
    print("Result:", result)

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc() # Print detailed traceback