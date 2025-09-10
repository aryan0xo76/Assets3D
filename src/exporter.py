"""Multi-format 3D model export utilities."""

import os
import logging
import numpy as np
import trimesh
from pathlib import Path
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class ModelExporter:
    def __init__(self):
        self.output_dir = Path("outputs")
        self.thumbnail_dir = self.output_dir / "thumbnails"
        
        self.output_dir.mkdir(exist_ok=True)
        self.thumbnail_dir.mkdir(exist_ok=True)
        logger.info(f"Export directory: {self.output_dir}")

    def export_model(self, mesh: trimesh.Trimesh, prompt: str, resolution: int) -> Dict[str, str]:
        """Export model in multiple formats"""
        try:
            timestamp = int(time.time())
            safe_prompt = self.make_safe_filename(prompt)
            filename_base = f"{safe_prompt}_{resolution}_{timestamp}"
            
            logger.info(f"Exporting model: {filename_base}")
            
            exports = {
                'filename_base': filename_base,
                'prompt': prompt,
                'resolution': resolution,
                'timestamp': timestamp
            }

            # Export different formats
            glb_path = self.export_glb(mesh, filename_base)
            if glb_path:
                exports['glb'] = str(glb_path)

            obj_path = self.export_obj(mesh, filename_base)
            if obj_path:
                exports['obj'] = str(obj_path)

            ply_path = self.export_ply(mesh, filename_base)
            if ply_path:
                exports['ply'] = str(ply_path)

            stl_path = self.export_stl(mesh, filename_base)
            if stl_path:
                exports['stl'] = str(stl_path)

            thumbnail_path = self.generate_thumbnail(mesh, filename_base)
            if thumbnail_path:
                exports['thumbnail'] = str(thumbnail_path)

            info_path = self.export_info(exports)
            if info_path:
                exports['info'] = str(info_path)

            logger.info(f"Export complete: {len(exports)-4} files generated")
            return exports

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {'error': str(e)}

    def make_safe_filename(self, prompt: str) -> str:
        """Convert prompt to safe filename"""
        import re
        
        words = prompt.lower().split()[:3]
        safe_words = []
        
        for word in words:
            clean_word = re.sub(r'[^a-z0-9]', '', word)
            if clean_word:
                safe_words.append(clean_word)
        
        result = '_'.join(safe_words) if safe_words else 'model'
        return result[:20]

    def export_glb(self, mesh: trimesh.Trimesh, filename_base: str) -> Optional[Path]:
        """Export as GLB format"""
        try:
            glb_path = self.output_dir / f"{filename_base}.glb"
            glb_data = mesh.export(file_type='glb')
            
            with open(glb_path, 'wb') as f:
                f.write(glb_data)
            
            logger.info(f"GLB: {glb_path}")
            return glb_path
            
        except Exception as e:
            logger.error(f"GLB export failed: {e}")
            return None

    def export_obj(self, mesh: trimesh.Trimesh, filename_base: str) -> Optional[Path]:
        """Export as OBJ format"""
        try:
            obj_path = self.output_dir / f"{filename_base}.obj"
            obj_data = mesh.export(file_type='obj')
            
            with open(obj_path, 'w') as f:
                f.write(obj_data)
            
            logger.info(f"OBJ: {obj_path}")
            return obj_path
            
        except Exception as e:
            logger.error(f"OBJ export failed: {e}")
            return None

    def export_ply(self, mesh: trimesh.Trimesh, filename_base: str) -> Optional[Path]:
        """Export as PLY format"""
        try:
            ply_path = self.output_dir / f"{filename_base}.ply"
            ply_data = mesh.export(file_type='ply')
            
            with open(ply_path, 'wb') as f:
                f.write(ply_data)
            
            logger.info(f"PLY: {ply_path}")
            return ply_path
            
        except Exception as e:
            logger.error(f"PLY export failed: {e}")
            return None

    def export_stl(self, mesh: trimesh.Trimesh, filename_base: str) -> Optional[Path]:
        """Export as STL format"""
        try:
            stl_path = self.output_dir / f"{filename_base}.stl"
            stl_data = mesh.export(file_type='stl')
            
            with open(stl_path, 'wb') as f:
                f.write(stl_data)
            
            logger.info(f"STL: {stl_path}")
            return stl_path
            
        except Exception as e:
            logger.error(f"STL export failed: {e}")
            return None

    def generate_thumbnail(self, mesh: trimesh.Trimesh, filename_base: str) -> Optional[Path]:
        """Generate thumbnail image"""
        try:
            thumbnail_path = self.thumbnail_dir / f"{filename_base}_thumb.png"
            
            scene = mesh.scene()
            scene.camera_transform = self.get_camera_transform(mesh)
            
            png_data = scene.save_image(
                resolution=[512, 512],
                visible=True
            )
            
            with open(thumbnail_path, 'wb') as f:
                f.write(png_data)
            
            logger.info(f"Thumbnail: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    def get_camera_transform(self, mesh: trimesh.Trimesh) -> np.ndarray:
        """Calculate optimal camera position for thumbnail"""
        try:
            bounds = mesh.bounds
            center = bounds.mean(axis=0)
            size = (bounds[1] - bounds[0]).max()
            
            if size == 0:
                size = 1.0
            
            distance = size * 2.5
            camera_pos = center + np.array([distance * 0.8, distance * 0.8, distance * 0.6])
            
            forward = center - camera_pos
            forward = forward / np.linalg.norm(forward)
            
            world_up = np.array([0, 0, 1])
            right = np.cross(forward, world_up)
            right = right / np.linalg.norm(right)
            
            up = np.cross(right, forward)
            
            transform = np.eye(4)
            transform[:3, 0] = right
            transform[:3, 1] = up
            transform[:3, 2] = -forward
            transform[:3, 3] = camera_pos
            
            return transform
            
        except Exception as e:
            logger.error(f"Camera transform calculation failed: {e}")
            return np.eye(4)

    def export_info(self, export_data: Dict) -> Optional[Path]:
        """Export model information"""
        try:
            filename_base = export_data.get('filename_base', 'model')
            info_path = self.output_dir / f"{filename_base}_info.txt"
            
            with open(info_path, 'w') as f:
                f.write("VoxelForge Model Information\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Prompt: {export_data.get('prompt', 'N/A')}\n")
                f.write(f"Resolution: {export_data.get('resolution', 'N/A')}\n")
                f.write(f"Generated: {export_data.get('timestamp', 'N/A')}\n")
                f.write(f"Base filename: {filename_base}\n\n")
                f.write("Available formats:\n")
                
                for key, value in export_data.items():
                    if key.endswith(('.glb', '.obj', '.ply', '.stl')):
                        f.write(f"  {key.upper()}: {value}\n")
                
                if 'thumbnail' in export_data:
                    f.write(f"  Thumbnail: {export_data['thumbnail']}\n")
            
            logger.info(f"Info: {info_path}")
            return info_path
            
        except Exception as e:
            logger.error(f"Info export failed: {e}")
            return None