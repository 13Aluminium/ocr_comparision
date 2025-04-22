import cv2
import numpy as np
import argparse
import os

def add_vertical_lines(image_path, output_path=None, line_spacing=20, line_thickness=1, line_color=(200, 200, 200)):
    """
    Add vertical lines to an image to potentially improve OCR for handwritten text.
    
    Args:
        image_path (str): Path to the input image
        output_path (str, optional): Path to save the output image. If None, creates a filename with prefix.
        line_spacing (int): Spacing between vertical lines in pixels
        line_thickness (int): Thickness of vertical lines in pixels
        line_color (tuple): BGR color of the lines (default: light gray)
        
    Returns:
        str: Path to the saved output image
    """
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    # Create a copy of the image to draw lines on
    img_with_lines = img.copy()
    
    # Get image dimensions
    height, width = img.shape[:2]
    
    # Draw vertical lines
    for x in range(0, width, line_spacing):
        cv2.line(img_with_lines, (x, 0), (x, height), line_color, line_thickness)
    
    # Save the image with lines
    if output_path is None:
        base_name = os.path.basename(image_path)
        file_name, ext = os.path.splitext(base_name)
        output_path = f"lined_{file_name}{ext}"
    
    cv2.imwrite(output_path, img_with_lines)
    return output_path

def adjust_line_contrast(image_path, output_path=None, line_spacing=20, line_thickness=1, 
                         line_color=(200, 200, 200), alpha=0.7):
    """
    Add vertical lines to an image with adjustable contrast to better blend with text.
    
    Args:
        image_path (str): Path to the input image
        output_path (str, optional): Path to save the output image
        line_spacing (int): Spacing between vertical lines in pixels
        line_thickness (int): Thickness of vertical lines in pixels
        line_color (tuple): BGR color of the lines
        alpha (float): Blending factor (0.0-1.0) - higher values show more original image
        
    Returns:
        str: Path to the saved output image
    """
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    # Create an empty image with same dimensions to draw lines
    line_img = np.zeros_like(img)
    
    # Get image dimensions
    height, width = img.shape[:2]
    
    # Draw vertical lines on the empty image
    for x in range(0, width, line_spacing):
        cv2.line(line_img, (x, 0), (x, height), line_color, line_thickness)
    
    # Blend the original image with the line image
    img_with_lines = cv2.addWeighted(img, alpha, line_img, 1 - alpha, 0)
    
    # Save the image with lines
    if output_path is None:
        base_name = os.path.basename(image_path)
        file_name, ext = os.path.splitext(base_name)
        output_path = f"lined_{file_name}{ext}"
    
    cv2.imwrite(output_path, img_with_lines)
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Add vertical lines to images to improve OCR')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('--output', '-o', help='Path to save the output image')
    parser.add_argument('--spacing', '-s', type=int, default=20, help='Spacing between vertical lines in pixels')
    parser.add_argument('--thickness', '-t', type=int, default=1, help='Thickness of vertical lines in pixels')
    parser.add_argument('--blend', '-b', action='store_true', help='Use alpha blending for smoother lines')
    parser.add_argument('--alpha', '-a', type=float, default=0.7, help='Alpha blending factor (0.0-1.0)')
    parser.add_argument('--color', '-c', type=int, nargs=3, default=[200, 200, 200], 
                        help='Line color in BGR format (e.g., 200 200 200 for light gray)')
    
    args = parser.parse_args()
    
    if args.blend:
        output_path = adjust_line_contrast(
            args.image_path, 
            args.output, 
            args.spacing, 
            args.thickness, 
            tuple(args.color),
            args.alpha
        )
    else:
        output_path = add_vertical_lines(
            args.image_path, 
            args.output, 
            args.spacing, 
            args.thickness, 
            tuple(args.color)
        )
    
    print(f"Image with vertical lines saved to: {output_path}")

if __name__ == "__main__":
    main()