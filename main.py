#!/usr/bin/env python3
"""VoxelForge - Text-to-3D model generator."""

import os
import sys
import logging
import time
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.generator import ShapEGenerator
from src.processor import MeshProcessor
from src.exporter import ModelExporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

class VoxelForge:
    def __init__(self):
        """Initialize VoxelForge pipeline"""
        logger.info("Initializing VoxelForge...")
        self.generator = ShapEGenerator()
        self.processor = MeshProcessor()
        self.exporter = ModelExporter()
        
        Path("models").mkdir(exist_ok=True)
        Path("outputs").mkdir(exist_ok=True)
        logger.info("VoxelForge ready")

    def generate_model(self, prompt: str, resolution: int = 32, quality: str = 'standard') -> bool:
        """Complete generation pipeline"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting generation: '{prompt}' (res: {resolution}, quality: {quality})")
            
            if quality == 'high':
                steps = 128
                guidance = 25.0
            else:
                steps = 64
                guidance = 15.0

            logger.info("Step 1/3: Generating 3D model with Shap-E...")
            mesh = self.generator.generate_from_text(prompt, steps=steps, guidance_scale=guidance)
            
            if mesh is None:
                logger.error("Failed to generate base mesh")
                return False

            logger.info("Step 2/3: Processing and enhancing mesh...")
            processed_mesh = self.processor.process_mesh(mesh)
            
            if processed_mesh is None:
                logger.error("Failed to process mesh")
                return False

            logger.info("Step 3/3: Exporting model...")
            export_result = self.exporter.export_model(
                processed_mesh, prompt, resolution
            )
            
            if 'error' in export_result:
                logger.error(f"Export failed: {export_result['error']}")
                return False

            generation_time = time.time() - start_time
            logger.info("Generation complete")
            self.print_results(export_result, generation_time)
            return True
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return False

    def print_results(self, export_result: dict, generation_time: float):
        """Print generation results"""
        print("\n" + "="*50)
        print("MODEL GENERATED SUCCESSFULLY")
        print("="*50)
        print(f"Prompt: {export_result.get('prompt', 'N/A')}")
        print(f"Time: {generation_time:.1f} seconds")
        print(f"Resolution: {export_result.get('resolution', 'N/A')}")
        print()
        print("Generated files:")
        
        file_types = {
            'glb': 'GLB (Web/Games)',
            'obj': 'OBJ (Universal)',
            'ply': 'PLY (Research)',
            'stl': 'STL (3D Print)',
            'thumbnail': 'Thumbnail'
        }
        
        for file_type, description in file_types.items():
            if file_type in export_result:
                print(f"  {description}: {export_result[file_type]}")
        
        if 'info' in export_result:
            print(f"  Info file: {export_result['info']}")
        
        print("\nModels saved in 'outputs/' directory")
        print("="*50 + "\n")

def get_user_input():
    """Get input from user"""
    print("VoxelForge - Text to 3D Model Generator")
    print("="*45)
    
    while True:
        prompt = input("\nEnter your text prompt: ").strip()
        if prompt:
            break
        print("Please enter a valid prompt!")

    while True:
        try:
            res_input = input("Enter resolution (default 32): ").strip()
            if not res_input:
                resolution = 32
                break
            
            resolution = int(res_input)
            if resolution > 0:
                break
            else:
                print("Resolution must be positive!")
        except ValueError:
            print("Please enter a valid number!")

    while True:
        quality_input = input("Quality - (s)tandard/(h)igh (default s): ").strip().lower()
        if not quality_input or quality_input == 's':
            quality = 'standard'
            break
        elif quality_input == 'h':
            quality = 'high'
            break
        else:
            print("Enter 's' for standard or 'h' for high!")
    
    return prompt, resolution, quality

def main():
    """Main application loop"""
    try:
        forge = VoxelForge()
        
        while True:
            try:
                prompt, resolution, quality = get_user_input()
                success = forge.generate_model(prompt, resolution, quality)
                
                if not success:
                    print("\nGeneration failed. Please try again.")

                print("\n" + "="*45)
                continue_input = input("Generate another model? (y/n): ").strip().lower()
                
                if continue_input not in ['y', 'yes']:
                    break
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"\nError: {e}")
                
                continue_input = input("Try again? (y/n): ").strip().lower()
                if continue_input not in ['y', 'yes']:
                    break
        
        print("Thanks for using VoxelForge!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()