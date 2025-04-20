$(document).ready(function() {
    const ocrForm = $('#ocrForm');
    const submitBtn = $('#submitBtn');
    const resultsSection = $('#resultsSection');
    const dropZone = $('#dropZone');
    const fileInput = $('#file');
    const imagePreview = $('#imagePreview');
    
    // Drag and drop functionality
    dropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });
    
    dropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });
    
    dropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            fileInput[0].files = files;
            handleFileSelect(files[0]);
        }
    });
    
    dropZone.on('click', function() {
        fileInput.click();
    });
    
    // Document type selection
    $('.document-type button').on('click', function() {
        $('.document-type button').removeClass('active');
        $(this).addClass('active');
        $('#fileType').val($(this).data('type'));
    });
    
    // File selection handling
    fileInput.on('change', function() {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });
    
    function handleFileSelect(file) {
        if (file) {
            // Update dropzone appearance
            dropZone.addClass('has-file');
            dropZone.find('.upload-text').text(file.name);
            dropZone.find('.upload-hint').first().text('Click to change file');
            
            // Show preview section
            $('#previewSection').show();
            
            // Update file type based on extension
            const extension = file.name.split('.').pop().toLowerCase();
            if (extension === 'pdf') {
                $('.document-type button[data-type="pdf"]').click();
            } else if (extension === 'jpg' || extension === 'jpeg' || extension === 'png') {
                $('.document-type button[data-type="image"]').click();
            }
            
            // Preview handling
            const reader = new FileReader();
            reader.onload = function(e) {
                if (file.type.includes('image')) {
                    const img = new Image();
                    img.onload = function() {
                        const maxWidth = imagePreview.width();
                        const maxHeight = window.innerHeight * 0.4;
                        const ratio = Math.min(maxWidth / img.width, maxHeight / img.height);
                        const width = img.width * ratio;
                        const height = img.height * ratio;
                        
                        imagePreview.html(`
                            <div class="preview-container">
                                <img src="${e.target.result}" 
                                     alt="Preview" 
                                     style="width: ${width}px; height: ${height}px;"
                                     class="preview-image">
                            </div>
                        `);
                    };
                    img.src = e.target.result;
                } else if (file.type === 'application/pdf') {
                    imagePreview.html(`
                        <div class="pdf-preview">
                            <i class="mdi mdi-file-pdf-box"></i>
                            <p class="pdf-name">${file.name}</p>
                        </div>
                    `);
                }
            };
            reader.readAsDataURL(file);
        }
    }

    function showImagePreview(src) {
        const maxHeight = Math.min(400, window.innerHeight * 0.4);
        imagePreview.html(`
            <div class="preview-container">
                <img src="${src}" alt="Preview" style="max-height: ${maxHeight}px;" class="preview-image">
            </div>
        `);
    }

    function showPdfPreview(filename) {
        imagePreview.html(`
            <div class="pdf-preview">
                <i class="mdi mdi-file-pdf-box"></i>
                <p class="pdf-name">Processing preview for: ${filename}</p>
            </div>
        `);
    }
    
    function updateFileType(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        let type = 'image';
        
        if (extension === 'pdf') {
            type = 'pdf';
            $('.document-type button[data-type="pdf"]').click();
        } else {
            $('.document-type button[data-type="image"]').click();
        }
        
        $('#fileType').val(type);
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Document type button handling
    $('.document-type button').on('click', function(e) {
        e.preventDefault();
        $('.document-type button').removeClass('active');
        $(this).addClass('active');
        $('#fileType').val($(this).data('type'));
    });

    // Improved drag and drop handling
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone[0].addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone[0].addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone[0].addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.addClass('dragover');
    }
    
    function unhighlight() {
        dropZone.removeClass('dragover');
    }
    
    // Handle both drop and click-to-select
    dropZone[0].addEventListener('drop', handleDrop, false);
    $('#file').on('change', function() {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            $('#file')[0].files = files;
            handleFileSelect(files[0]);
        }
    }
    
    // Form submission
    ocrForm.on('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        submitBtn.prop('disabled', true);
        submitBtn.html('<div class="spinner-border spinner-border-sm me-2" role="status"></div>Processing...');
        
        // Prepare form data
        const formData = new FormData(this);
        
        // Send AJAX request
        $.ajax({
            url: '/process',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: handleOCRResponse,
            error: function(xhr, status, error) {
                showError('An error occurred while processing: ' + error);
            },
            complete: function() {
                // Reset button state
                submitBtn.prop('disabled', false);
                submitBtn.html('<i class="mdi mdi-text-recognition"></i> Process with All OCR Libraries');
            }
        });
    });
    
    function createLibraryCard(library, result) {
        const libraryName = library.charAt(0).toUpperCase() + library.slice(1);
        const hasError = typeof result === 'string' && result.toLowerCase().includes('error');
        
        let libraryIcon = '';
        switch(library) {
            case 'pytesseract': libraryIcon = 'mdi-google-lens'; break;
            case 'easyocr': libraryIcon = 'mdi-text-recognition'; break;
            case 'paddleocr': libraryIcon = 'mdi-paddle'; break;
            case 'doctr': libraryIcon = 'mdi-file-document-outline'; break;
        }

        const formattedResult = formatResult(result, library);
        const textLength = typeof result === 'string' ? result.length : JSON.stringify(result).length;
        const shouldCollapse = textLength > 500; // Threshold for collapsing text
        const initialHeight = shouldCollapse ? '400px' : 'auto';
        
        let resultContent = '';
        if (!hasError) {
            resultContent = `
                <div class="result-text" style="max-height: ${initialHeight}" data-full-text="${escapeHtml(JSON.stringify(result))}">
                    ${formattedResult}
                </div>
                ${shouldCollapse ? `
                    <button class="expand-button visible" data-expanded="false">
                        <i class="mdi mdi-chevron-down"></i>
                        Show More
                    </button>
                ` : ''}
                <div class="text-length-indicator">
                    <i class="mdi mdi-text-box-outline"></i>
                    <span>${formatTextLength(textLength)}</span>
                </div>`;
        }

        return `
            <div class="library-card ${hasError ? 'has-error' : ''}">
                <div class="card-header">
                    <i class="mdi ${libraryIcon}"></i>
                    <h5>${libraryName}</h5>
                    ${!hasError ? `
                        <button class="btn btn-icon copy-btn" data-result="${library}">
                            <i class="mdi mdi-content-copy"></i>
                        </button>
                    ` : ''}
                </div>
                <div class="card-content">
                    ${hasError ? 
                        `<div class="error-message">${result}</div>` : 
                        resultContent
                    }
                </div>
            </div>
        `;
    }

    function formatTextLength(length) {
        if (length < 1000) return `${length} characters`;
        return `${(length / 1000).toFixed(1)}K characters`;
    }

    // Add event listener for expand/collapse buttons
    $(document).on('click', '.expand-button', function() {
        const button = $(this);
        const resultText = button.siblings('.result-text');
        const isExpanded = button.data('expanded');
        
        if (isExpanded) {
            resultText.css('max-height', '400px');
            button.html('<i class="mdi mdi-chevron-down"></i> Show More');
            button.data('expanded', false);
        } else {
            resultText.css('max-height', 'none');
            button.html('<i class="mdi mdi-chevron-up"></i> Show Less');
            button.data('expanded', true);
        }
    });

    function handleOCRResponse(response) {
        if (response.error) {
            showError(response.error);
            return;
        }

        // Update image preview if URL is provided
        if (response.preview_url) {
            $('#previewSection').show();
            showImagePreview(response.preview_url);
        }
        
        // Process OCR results
        let resultsHtml = '';
        Object.entries(response).forEach(([key, value]) => {
            if (key !== 'preview_url') {
                resultsHtml += createLibraryCard(key, value);
            }
        });
        
        $('.libraries-grid').html(resultsHtml);
        resultsSection.show();
        
        // Smooth scroll to results
        resultsSection[0].scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start'
        });
    }

    function formatResult(result, library) {
        if (typeof result !== 'string') {
            try {
                return formatJsonResult(result);
            } catch (e) {
                return JSON.stringify(result, null, 2);
            }
        }
        return escapeHtml(result);
    }
    
    function formatJsonResult(data) {
        if (Array.isArray(data)) {
            return data.map(item => escapeHtml(item)).join('<br>');
        }
        
        let html = '<div class="json-data">';
        for (const [key, value] of Object.entries(data)) {
            const formattedKey = key.replace(/_/g, ' ');
            if (Array.isArray(value)) {
                html += `<div class="json-array">
                    <strong>${formattedKey}:</strong>
                    <ul>${value.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
                </div>`;
            } else {
                html += `<div class="json-field">
                    <strong>${formattedKey}:</strong>
                    <span>${value ? escapeHtml(value) : '<em>Not detected</em>'}</span>
                </div>`;
            }
        }
        html += '</div>';
        return html;
    }
    
    function showError(message) {
        $('.libraries-grid').html(`
            <div class="error-card">
                <i class="mdi mdi-alert-circle"></i>
                <h5>Error</h5>
                <p>${message}</p>
            </div>
        `);
    }
    
    function escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Initialize copy buttons
    $(document).on('click', '.copy-btn', function() {
        const libraryName = $(this).data('result');
        const textToCopy = $(this).closest('.library-card').find('.result-text').text();
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            const icon = $(this).find('i');
            icon.removeClass('mdi-content-copy').addClass('mdi-check');
            
            setTimeout(() => {
                icon.removeClass('mdi-check').addClass('mdi-content-copy');
            }, 1500);
        });
    });
    
    // Ensure proper cleanup when switching files
    function resetUI() {
        $('#imagePreview').empty();
        $('#previewSection').hide();
        $('.libraries-grid').empty();
        $('#resultsSection').hide();
        $('#submitBtn').prop('disabled', false)
            .html('<i class="mdi mdi-text-recognition"></i> Process with All OCR Libraries');
    }
    
    // Handle window resize for responsive previews
    let resizeTimeout;
    $(window).on('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            const file = $('#file')[0].files[0];
            if (file && file.type.includes('image')) {
                handleFileSelect(file); // Recalculate image preview size
            }
        }, 250);
    });
});