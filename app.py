from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import pdf2image
import tempfile

# Import OCR modules
import pytesseract_module
import easyocr_module
import doctr_module

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'static/temp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_preview_image(file_path, original_filename):
    """Create a preview image for PDF files"""
    if original_filename.lower().endswith('.pdf'):
        # Convert first page of PDF to image
        images = pdf2image.convert_from_path(file_path, first_page=1, last_page=1)
        if images:
            preview_path = os.path.join(app.config['TEMP_FOLDER'], 
                                      f"{os.path.splitext(original_filename)[0]}_preview.jpg")
            images[0].save(preview_path, 'JPEG')
            return url_for('static', filename=f"temp/{os.path.basename(preview_path)}")
    else:
        # For regular images, just return the URL
        return url_for('static', filename=f"temp/{os.path.basename(file_path)}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        temp_path = os.path.join(app.config['TEMP_FOLDER'], filename)
        
        # Save file in both upload and temp folders
        file.save(filepath)
        file.seek(0)
        file.save(temp_path)
        
        # Create preview image for PDF or get image URL
        preview_url = create_preview_image(filepath, filename)
        
        # Get selected OCR method
        ocr_method = request.form.get('ocr_method', 'all')
        file_type = request.form.get('file_type', 'image')
        
        results = {
            'preview_url': preview_url
        }
        
        if ocr_method in ['all', 'pytesseract']:
            try:
                if file_type == 'image':
                    results['pytesseract'] = pytesseract_module.extract_text_from_image(filepath)
                elif file_type == 'pdf':
                    results['pytesseract'] = pytesseract_module.extract_text_from_pdf(filepath)
                elif file_type == 'handwriting':
                    results['pytesseract'] = pytesseract_module.recognize_handwriting(filepath)
                elif file_type == 'invoice':
                    results['pytesseract'] = pytesseract_module.extract_invoice_data(filepath)
            except Exception as e:
                results['pytesseract'] = f"Error: {str(e)}"
        
        if ocr_method in ['all', 'easyocr']:
            try:
                if file_type == 'image':
                    results['easyocr'] = easyocr_module.extract_text_from_image(filepath)
                elif file_type == 'pdf':
                    results['easyocr'] = easyocr_module.extract_text_from_pdf(filepath)
                elif file_type == 'handwriting':
                    results['easyocr'] = easyocr_module.recognize_handwriting(filepath)
                elif file_type == 'invoice':
                    results['easyocr'] = easyocr_module.extract_invoice_data(filepath)
            except Exception as e:
                results['easyocr'] = f"Error: {str(e)}"
        
        if ocr_method in ['all', 'doctr']:
            try:
                if file_type == 'image':
                    results['doctr'] = doctr_module.extract_text_from_image(filepath)
                elif file_type == 'pdf':
                    results['doctr'] = doctr_module.extract_text_from_pdf(filepath)
                elif file_type == 'handwriting':
                    results['doctr'] = doctr_module.recognize_handwriting(filepath)
                elif file_type == 'invoice':
                    results['doctr'] = doctr_module.extract_invoice_data(filepath)
            except Exception as e:
                results['doctr'] = f"Error: {str(e)}"
                
        return jsonify(results)
    
    return jsonify({'error': 'File type not allowed'})

# Clean up temporary files periodically (you might want to add a cleanup schedule)
def cleanup_temp_files():
    temp_folder = app.config['TEMP_FOLDER']
    for file in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Error deleting {file_path}: {e}')

if __name__ == '__main__':
    app.run(debug=True)