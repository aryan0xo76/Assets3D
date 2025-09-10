#!/usr/bin/env python3
"""Model setup utility for VoxelForge."""

import subprocess
import sys
import os
import urllib.request
from pathlib import Path

def install_shap_e():
    """Install Shap-E package"""
    print("Installing Shap-E...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/openai/shap-e.git"])
    print("Shap-E installed")

def download_models_directly():
    """Download Shap-E models to local directory"""
    print("Downloading models...")
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    models = {
        "transmitter.pkl": "https://openaipublic.azureedge.net/shap-e/checkpoints/transmitter.pkl",
        "text300M.pkl": "https://openaipublic.azureedge.net/shap-e/checkpoints/text300M.pkl",
        "diffusion_config.json": "https://openaipublic.azureedge.net/shap-e/configs/diffusion.yaml"
    }

    for filename, url in models.items():
        local_path = models_dir / filename
        if local_path.exists():
            print(f"{filename} already exists")
            continue
            
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, local_path)
            size_mb = local_path.stat().st_size / (1024 * 1024)
            print(f"Downloaded {filename} ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

def main():
    install_shap_e()
    download_models_directly()
    
    print(f"\nModels downloaded to: {Path('models').absolute()}")
    print("Contents:")
    for file in Path("models").iterdir():
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  {file.name} ({size_mb:.1f}MB)")

if __name__ == "__main__":
    main()