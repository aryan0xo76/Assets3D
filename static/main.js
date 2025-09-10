/**
 * VoxelForge Web Interface - Main JavaScript
 */

let currentJobId = null;
let progressInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('VoxelForge Web Interface initialized');
    loadRecentModels();
});

function startGeneration() {
    const prompt = document.getElementById('prompt').value.trim();
    const quality = document.getElementById('quality').value;
    
    if (!prompt) {
        alert('Please enter a text prompt!');
        return;
    }
    
    console.log(`Starting generation: "${prompt}" (${quality})`);
    
    showProgressSection(true);
    showResultsSection(false);
    disableGenerateButton(true);
    updateProgress(0, 'Starting generation...');
    
    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            quality: quality
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentJobId = data.job_id;
        console.log(`Generation started: ${currentJobId}`);
        
        startProgressPolling();
    })
    .catch(error => {
        console.error('Generation failed:', error);
        alert(`Generation failed: ${error.message}`);
        resetGenerationUI();
    });
}

function startProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(() => {
        if (!currentJobId) {
            stopProgressPolling();
            return;
        }
        
        fetch(`/status/${currentJobId}`)
            .then(response => response.json())
            .then(data => {
                updateProgress(data.progress || 0, data.message || 'Processing...');
                
                if (data.status === 'completed') {
                    onGenerationComplete(data);
                } else if (data.status === 'error') {
                    onGenerationError(data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Status check failed:', error);
                onGenerationError('Failed to check status');
            });
    }, 2000);
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function onGenerationComplete(data) {
    console.log('Generation completed:', data);
    
    stopProgressPolling();
    updateProgress(100, 'Generation completed!');
    
    setTimeout(() => {
        showProgressSection(false);
        showResultsSection(true, data.files);
        disableGenerateButton(false);
        
        if (data.files && data.files.ply) {
            loadModelInViewer(data.files.ply);
        }
        
        loadRecentModels();
        
    }, 1000);
}

function onGenerationError(errorMessage) {
    console.error('Generation error:', errorMessage);
    
    stopProgressPolling();
    alert(`Generation failed: ${errorMessage}`);
    resetGenerationUI();
}

function cancelGeneration() {
    console.log('Cancelling generation');
    
    currentJobId = null;
    stopProgressPolling();
    resetGenerationUI();
}

function loadModelInViewer(filename) {
    if (!viewer) {
        console.error('3D viewer not available');
        return;
    }
    
    console.log(`Loading model in viewer: ${filename}`);
    
    viewer.loadPLY(filename, 
        (progress) => {
            console.log('Loading progress:', progress);
        },
        () => {
            console.log('Model loaded in viewer');
        }
    );
}

function loadRecentModels() {
    fetch('/list_models')
        .then(response => response.json())
        .then(data => {
            updateModelGallery(data.models || []);
        })
        .catch(error => {
            console.error('Failed to load recent models:', error);
        });
}

function updateModelGallery(models) {
    const gallery = document.getElementById('modelGallery');
    
    if (models.length === 0) {
        gallery.innerHTML = '<p class="no-models">No models generated yet</p>';
        return;
    }
    
    const html = models.map(model => `
        <div class="gallery-item" onclick="loadModelInViewer('${model.ply}')">
            <div class="gallery-thumb">🎲</div>
            <div class="gallery-info">
                <div class="gallery-name">${model.name}</div>
                <div class="gallery-date">${new Date(model.created * 1000).toLocaleDateString()}</div>
            </div>
        </div>
    `).join('');
    
    gallery.innerHTML = html;
}

function resetForm() {
    document.getElementById('prompt').value = '';
    document.getElementById('quality').value = 'standard';
    showResultsSection(false);
    
    if (viewer) {
        viewer.hideMessage();
        if (viewer.currentMesh) {
            viewer.scene.remove(viewer.currentMesh);
            viewer.currentMesh = null;
        }
        
        const placeholderHtml = `
            <div class="viewer-placeholder">
                <div class="placeholder-icon">🎲</div>
                <h3>Ready to Generate</h3>
                <p>Enter a text prompt and click "Generate Model" to see your 3D creation here.</p>
            </div>
        `;
        viewer.showMessage(placeholderHtml);
    }
    
    console.log('Form reset for new generation');
}

function updateProgress(progress, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill) {
        progressFill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
    }
    
    if (progressText) {
        progressText.textContent = message;
    }
    
    console.log(`Progress: ${progress}% - ${message}`);
}

function showProgressSection(show) {
    const section = document.getElementById('progressSection');
    if (section) {
        section.style.display = show ? 'block' : 'none';
    }
}

function showResultsSection(show, files = null) {
    const section = document.getElementById('resultsSection');
    if (section) {
        section.style.display = show ? 'block' : 'none';
    }
    
    if (show && files) {
        const formats = ['ply', 'glb', 'obj'];
        formats.forEach(format => {
            const link = document.getElementById(`download${format.charAt(0).toUpperCase() + format.slice(1)}`);
            if (link && files[format]) {
                link.href = `/download/${files[format]}/attachment`;
                link.style.display = 'inline-block';
            } else if (link) {
                link.style.display = 'none';
            }
        });
    }
}

function disableGenerateButton(disabled) {
    const btn = document.getElementById('generateBtn');
    if (btn) {
        btn.disabled = disabled;
        btn.textContent = disabled ? 'Generating...' : 'Generate Model';
    }
}

function resetGenerationUI() {
    showProgressSection(false);
    showResultsSection(false);
    disableGenerateButton(false);
    currentJobId = null;
}

// Handle Enter key in prompt textarea
document.addEventListener('keydown', (event) => {
    if (event.target.id === 'prompt' && event.key === 'Enter' && event.ctrlKey) {
        event.preventDefault();
        startGeneration();
    }
});

// Add prompt suggestion functionality
function setPrompt(text) {
    document.getElementById('prompt').value = text;
}

// Gallery item styling
const galleryStyle = document.createElement('style');
galleryStyle.textContent = `
    .gallery-item {
        display: flex;
        align-items: center;
        padding: 10px;
        margin-bottom: 8px;
        background: #f8f9fa;
        border-radius: 6px;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    
    .gallery-item:hover {
        background: #e9ecef;
    }
    
    .gallery-thumb {
        width: 40px;
        height: 40px;
        background: #dee2e6;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-right: 12px;
    }
    
    .gallery-info {
        flex: 1;
    }
    
    .gallery-name {
        font-size: 13px;
        font-weight: 500;
        color: #333;
        margin-bottom: 2px;
    }
    
    .gallery-date {
        font-size: 11px;
        color: #6c757d;
    }
`;
document.head.appendChild(galleryStyle);