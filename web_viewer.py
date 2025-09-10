#!/usr/bin/env python3
"""VoxelForge web interface - local Flask server."""

import os
import sys
import json
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from main import VoxelForge

app = Flask(__name__)
app.config['SECRET_KEY'] = 'voxelforge-local-viewer-2025'

active_jobs = {}
job_counter = 0
forge = None

def initialize_forge():
    """Initialize VoxelForge instance"""
    global forge
    try:
        forge = VoxelForge()
        print("VoxelForge initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize VoxelForge: {e}")
        return False

def generate_model_background(job_id, prompt, quality):
    """Background thread for model generation"""
    global active_jobs, forge
    
    try:
        active_jobs[job_id]['status'] = 'generating'
        active_jobs[job_id]['message'] = 'Generating 3D model...'
        active_jobs[job_id]['progress'] = 10
        
        success = forge.generate_model(prompt, 32, quality)
        
        if success:
            outputs_dir = Path('outputs')
            if outputs_dir.exists():
                files = list(outputs_dir.glob('*'))
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                ply_files = [f for f in files if f.suffix == '.ply']
                glb_files = [f for f in files if f.suffix == '.glb']
                obj_files = [f for f in files if f.suffix == '.obj']
                
                if ply_files:
                    active_jobs[job_id]['status'] = 'completed'
                    active_jobs[job_id]['message'] = 'Generation completed!'
                    active_jobs[job_id]['progress'] = 100
                    active_jobs[job_id]['files'] = {
                        'ply': ply_files[0].name if ply_files else None,
                        'glb': glb_files[0].name if glb_files else None,
                        'obj': obj_files[0].name if obj_files else None,
                    }
                else:
                    active_jobs[job_id]['status'] = 'error'
                    active_jobs[job_id]['message'] = 'No PLY file generated'
            else:
                active_jobs[job_id]['status'] = 'error'
                active_jobs[job_id]['message'] = 'Output directory not found'
        else:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['message'] = 'Model generation failed'
            
    except Exception as e:
        active_jobs[job_id]['status'] = 'error'
        active_jobs[job_id]['message'] = f'Generation error: {str(e)}'
        print(f"Generation error for job {job_id}: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    global job_counter, active_jobs
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        quality = data.get('quality', 'standard')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if not forge:
            return jsonify({'error': 'VoxelForge not initialized'}), 500
        
        job_counter += 1
        job_id = f"job_{job_counter}_{int(time.time())}"
        
        active_jobs[job_id] = {
            'status': 'starting',
            'message': 'Initializing generation...',
            'progress': 0,
            'prompt': prompt,
            'quality': quality,
            'files': {}
        }
        
        thread = threading.Thread(
            target=generate_model_background,
            args=(job_id, prompt, quality)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Generation started'
        })
        
    except Exception as e:
        print(f"Generate endpoint error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    return jsonify(job)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        outputs_dir = Path('outputs')
        file_path = outputs_dir / filename
        
        if not file_path.exists():
            abort(404)
        
        return send_file(file_path, as_attachment=False)
        
    except Exception as e:
        print(f"Download error: {e}")
        abort(500)

@app.route('/download/<filename>/attachment')
def download_file_attachment(filename):
    try:
        outputs_dir = Path('outputs')
        file_path = outputs_dir / filename
        
        if not file_path.exists():
            abort(404)
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"Download error: {e}")
        abort(500)

@app.route('/list_models')
def list_models():
    try:
        outputs_dir = Path('outputs')
        if not outputs_dir.exists():
            return jsonify({'models': []})
        
        models = []
        ply_files = list(outputs_dir.glob('*.ply'))
        
        for ply_file in sorted(ply_files, key=lambda x: x.stat().st_mtime, reverse=True):
            base_name = ply_file.stem
            models.append({
                'name': base_name,
                'ply': ply_file.name,
                'created': ply_file.stat().st_mtime
            })
        
        return jsonify({'models': models[:10]})
        
    except Exception as e:
        print(f"List models error: {e}")
        return jsonify({'models': []})

def main():
    """Start the web viewer"""
    print("VoxelForge Web Viewer")
    print("=" * 40)
    
    outputs_dir = Path('outputs')
    if not outputs_dir.exists():
        outputs_dir.mkdir()
        print("Created outputs directory")
    
    print("Initializing VoxelForge...")
    if not initialize_forge():
        print("Failed to start - VoxelForge initialization failed")
        return
    
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down VoxelForge Web Viewer")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == '__main__':
    main()