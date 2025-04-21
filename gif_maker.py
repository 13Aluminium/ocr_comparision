import os
import argparse
from PIL import Image
import glob
import re

def natural_sort_key(s):
    """Sort strings with numbers in natural order (e.g., 1, 2, 10 instead of 1, 10, 2)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def create_gif_from_images(input_folder, output_file, duration=200, loop=0, sort_naturally=True):
    """
    Create a GIF animation from JPG images in a folder.
    
    Parameters:
    - input_folder: Path to folder containing JPG images
    - output_file: Path for the output GIF file
    - duration: Duration of each frame in milliseconds (default: 200ms)
    - loop: Number of times to loop the GIF (0 means infinite)
    - sort_naturally: If True, sort filenames in natural order (1, 2, 10 vs 1, 10, 2)
    
    Returns:
    - Path to the created GIF file
    """
    try:
        # Get list of JPG files in the folder
        jpg_files = glob.glob(os.path.join(input_folder, "*.jpg"))
        
        # Sort files
        if sort_naturally:
            jpg_files.sort(key=natural_sort_key)
        else:
            jpg_files.sort()
        
        if not jpg_files:
            return f"No JPG files found in {input_folder}"
        
        # Open all images
        images = []
        for file in jpg_files:
            try:
                img = Image.open(file)
                images.append(img.copy())  # Create a copy to avoid "seek" issues
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
        
        if not images:
            return "No valid images found"
        
        # Save as GIF
        images[0].save(
            output_file, 
            save_all=True, 
            append_images=images[1:], 
            duration=duration, 
            loop=loop,
            optimize=False  # Set to True for smaller file size but may reduce quality
        )
        
        return output_file
    except Exception as e:
        return f"Error creating GIF: {str(e)}"

def create_gif_with_progress(input_folder, output_file, duration=200, loop=0, resize=None):
    """
    Create a GIF with progress reporting for large numbers of images.
    
    Parameters:
    - input_folder: Path to folder containing JPG images
    - output_file: Path for the output GIF file
    - duration: Duration of each frame in milliseconds
    - loop: Number of times to loop the GIF (0 means infinite)
    - resize: Tuple (width, height) to resize images before creating GIF, or None for no resizing
    
    Returns:
    - Path to the created GIF file
    """
    try:
        # Get list of JPG files in the folder
        jpg_files = glob.glob(os.path.join(input_folder, "*.jpg"))
        jpg_files.sort(key=natural_sort_key)
        
        if not jpg_files:
            return f"No JPG files found in {input_folder}"
        
        print(f"Processing {len(jpg_files)} images...")
        
        # Open first image to get size for the GIF
        first_img = Image.open(jpg_files[0])
        if resize:
            img_size = resize
            first_img = first_img.resize(resize, Image.LANCZOS)
        else:
            img_size = first_img.size
        
        # Prepare frames
        frames = []
        total_files = len(jpg_files)
        
        for i, file in enumerate(jpg_files):
            if i % 10 == 0 or i == total_files - 1:
                print(f"Processing image {i+1}/{total_files} ({(i+1)/total_files*100:.1f}%)")
            
            try:
                img = Image.open(file)
                if resize:
                    img = img.resize(img_size, Image.LANCZOS)
                frames.append(img.copy())
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
        
        if not frames:
            return "No valid images found"
        
        print(f"Saving GIF to {output_file}...")
        
        # Save as GIF
        frames[0].save(
            output_file, 
            format='GIF',
            save_all=True, 
            append_images=frames[1:], 
            duration=duration, 
            loop=loop,
            optimize=False
        )
        
        print(f"GIF created successfully: {output_file}")
        return output_file
    except Exception as e:
        return f"Error creating GIF: {str(e)}"

def ocr_visualization_to_gif(visualization_dir, output_file, duration=500, include_composite=False):
    """
    Convert OCR row visualization images to a GIF showing the progression.
    
    Parameters:
    - visualization_dir: Directory containing row visualization images
    - output_file: Path for the output GIF file
    - duration: Frame duration in milliseconds
    - include_composite: Whether to include the composite image as the final frame
    
    Returns:
    - Path to the created GIF file
    """
    try:
        # Get individual row images
        row_images = glob.glob(os.path.join(visualization_dir, "row_*.jpg"))
        row_images.sort(key=natural_sort_key)
        
        if not row_images:
            return f"No row visualization images found in {visualization_dir}"
        
        # Check if we should include the composite image
        if include_composite:
            composite_image = os.path.join(visualization_dir, "all_selected_rows.jpg")
            if os.path.exists(composite_image):
                row_images.append(composite_image)
        
        # Process images
        frames = []
        for img_path in row_images:
            img = Image.open(img_path)
            frames.append(img.copy())
        
        # Save as GIF
        frames[0].save(
            output_file,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0  # Loop forever
        )
        
        return output_file
    except Exception as e:
        return f"Error creating visualization GIF: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create GIF from JPG images in a folder')
    parser.add_argument('input_folder', help='Folder containing JPG images')
    parser.add_argument('output_file', help='Output GIF file path')
    parser.add_argument('--duration', type=int, default=200, 
                        help='Duration of each frame in milliseconds (default: 200)')
    parser.add_argument('--loop', type=int, default=0,
                        help='Number of times to loop (0 = infinite, default: 0)')
    parser.add_argument('--resize', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                        help='Resize images to specified width and height')
    parser.add_argument('--ocr-viz', action='store_true',
                        help='Process as OCR visualization output')
    parser.add_argument('--include-composite', action='store_true',
                        help='Include the composite visualization as final frame')
    
    args = parser.parse_args()
    
    if args.ocr_viz:
        result = ocr_visualization_to_gif(
            args.input_folder, 
            args.output_file, 
            args.duration,
            args.include_composite
        )
    else:
        resize_tuple = tuple(args.resize) if args.resize else None
        result = create_gif_with_progress(
            args.input_folder, 
            args.output_file, 
            args.duration, 
            args.loop,
            resize_tuple
        )
    
    if result == args.output_file:
        print(f"GIF created successfully: {result}")
    else:
        print(result)