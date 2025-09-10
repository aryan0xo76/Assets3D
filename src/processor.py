"""Mesh processing and enhancement utilities."""

import logging
import numpy as np
import trimesh
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from typing import Optional

logger = logging.getLogger(__name__)

class MeshProcessor:
    def __init__(self, palette_size: int = 256):
        logger.info(f"Initialized with {palette_size} color palette")
        self.color_palette = self.generate_full_spectrum_palette(palette_size)

    def generate_full_spectrum_palette(self, size: int) -> np.ndarray:
        """Generate vibrant full RGB spectrum palette"""
        if size <= 216:
            # Create RGB cube with even steps
            steps = int(np.round(size ** (1/3)))
            values = np.linspace(0, 255, steps, dtype=int)
            
            palette = []
            for r in values:
                for g in values:
                    for b in values:
                        palette.append([r, g, b])
                        if len(palette) >= size:
                            break
                    if len(palette) >= size:
                        break
                if len(palette) >= size:
                    break
                    
        else:
            # Use HSV-based generation for larger palettes
            palette = []
            hue_steps = int(np.sqrt(size * 2))
            sat_steps = max(2, size // hue_steps // 2)
            val_steps = max(2, size // hue_steps // sat_steps)
            
            for h in np.linspace(0, 360, hue_steps, endpoint=False):
                for s in np.linspace(0.6, 1.0, sat_steps):
                    for v in np.linspace(0.7, 1.0, val_steps):
                        rgb = self.hsv_to_rgb(h/360, s, v)
                        palette.append((rgb * 255).astype(int))
                        
                        if len(palette) >= size:
                            break
                    if len(palette) >= size:
                        break
                if len(palette) >= size:
                    break
        
        # Fill remaining slots if needed
        while len(palette) < size:
            h = np.random.random()
            s = np.random.uniform(0.8, 1.0)
            v = np.random.uniform(0.8, 1.0)
            rgb = self.hsv_to_rgb(h, s, v)
            palette.append((rgb * 255).astype(int))
        
        return np.array(palette[:size], dtype=np.uint8)

    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        import colorsys
        return np.array(colorsys.hsv_to_rgb(h, s, v))

    def enhance_sharpness(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Enhance mesh sharpness by preserving sharp edges"""
        try:
            vertices = mesh.vertices.copy()
            faces = mesh.faces
            
            # Apply edge-preserving smoothing iterations
            for iteration in range(3):
                new_vertices = vertices.copy()
                
                for i, vertex in enumerate(vertices):
                    neighbor_faces = faces[np.any(faces == i, axis=1)]
                    if len(neighbor_faces) == 0:
                        continue
                    
                    neighbors = np.unique(neighbor_faces.flatten())
                    neighbors = neighbors[neighbors != i]
                    
                    if len(neighbors) > 0:
                        # Calculate vertex angles to detect sharp features
                        vertex_edges = []
                        for neighbor in neighbors:
                            edge_vec = vertices[neighbor] - vertex
                            vertex_edges.append(edge_vec)
                        
                        # Check if vertex is on sharp edge
                        is_sharp = False
                        if len(vertex_edges) >= 2:
                            for j in range(len(vertex_edges)-1):
                                angle = np.arccos(np.clip(
                                    np.dot(vertex_edges[j], vertex_edges[j+1]) / 
                                    (np.linalg.norm(vertex_edges[j]) * np.linalg.norm(vertex_edges[j+1])),
                                    -1.0, 1.0
                                ))
                                if angle > np.pi/3:  # 60 degrees
                                    is_sharp = True
                                    break
                        
                        # Apply smoothing only to non-sharp vertices
                        if not is_sharp:
                            neighbor_positions = vertices[neighbors]
                            smoothed_position = neighbor_positions.mean(axis=0)
                            new_vertices[i] = 0.8 * vertex + 0.2 * smoothed_position
                
                vertices = new_vertices
            
            enhanced_mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=faces,
                vertex_colors=mesh.visual.vertex_colors
            )
            
            logger.info("Applied sharpness enhancement")
            return enhanced_mesh
            
        except Exception as e:
            logger.warning(f"Sharpness enhancement failed: {e}")
            return mesh

    def process_mesh(self, mesh: trimesh.Trimesh) -> Optional[trimesh.Trimesh]:
        try:
            logger.info("Processing mesh...")
            
            # Clean mesh
            cleaned_mesh = self.clean_mesh(mesh)
            if cleaned_mesh is None:
                return None
            
            # Normalize scale and position
            normalized_mesh = self.normalize_mesh(cleaned_mesh)
            
            # Enhance sharpness
            sharpened_mesh = self.enhance_sharpness(normalized_mesh)
            
            # Enhance colors
            final_mesh = self.enhance_colors(sharpened_mesh)
            
            logger.info("Mesh processing complete")
            return final_mesh
            
        except Exception as e:
            logger.error(f"Mesh processing failed: {e}")
            return None

    def clean_mesh(self, mesh: trimesh.Trimesh) -> Optional[trimesh.Trimesh]:
        """Clean and repair mesh while preserving sharp features"""
        try:
            logger.info(f"Cleaning mesh ({len(mesh.vertices)} vertices, {len(mesh.faces)} faces)")
            
            # Remove degenerate faces
            mesh.remove_degenerate_faces()
            
            # Remove unreferenced vertices
            mesh.remove_unreferenced_vertices()
            
            # Keep only largest connected component
            components = mesh.split(only_watertight=False)
            if len(components) > 1:
                largest = max(components, key=lambda x: len(x.vertices))
                mesh = largest
                logger.info(f"Kept largest component: {len(mesh.vertices)} vertices")
            
            # Fix normals but preserve topology
            mesh.fix_normals()
            
            # Minimal vertex merging to preserve sharp details
            mesh.merge_vertices(merge_tex=False, merge_norm=False)
            
            logger.info(f"Cleaned mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
            return mesh
            
        except Exception as e:
            logger.error(f"Mesh cleaning failed: {e}")
            return None

    def normalize_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Normalize mesh to unit cube centered at origin"""
        try:
            bounds = mesh.bounds
            center = bounds.mean(axis=0)
            scale = (bounds[1] - bounds[0]).max()
            
            if scale == 0:
                logger.warning("Mesh has zero scale, using default")
                scale = 1.0
            
            mesh.vertices = (mesh.vertices - center) / (scale * 0.5)
            
            logger.info(f"Normalized mesh (scale factor: {scale:.3f})")
            return mesh
            
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return mesh

    def enhance_colors(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Enhanced colors with full RGB spectrum palette"""
        try:
            if mesh.visual.vertex_colors is None:
                # Apply random colors from full RGB palette
                colors = np.random.choice(len(self.color_palette), len(mesh.vertices))
                vertex_colors = np.array([self.color_palette[c] for c in colors])
                vertex_colors = np.column_stack([vertex_colors, np.full(len(vertex_colors), 255)])
                
                enhanced_mesh = mesh.copy()
                enhanced_mesh.visual.vertex_colors = vertex_colors.astype(np.uint8)
                return enhanced_mesh
            else:
                # Use original vertex colors from full RGB spectrum
                enhanced_mesh = mesh.copy()
                enhanced_mesh.visual.vertex_colors = mesh.visual.vertex_colors
                logger.info("Using original vertex colors from full RGB spectrum")
                return enhanced_mesh
                
        except Exception as e:
            logger.warning(f"Color enhancement failed: {e}")
            return mesh

    def generate_positional_colors(self, vertices: np.ndarray) -> np.ndarray:
        """Generate colors based on vertex positions"""
        try:
            colors = []
            for vertex in vertices:
                hash_val = hash(tuple(vertex.round(decimals=2))) % len(self.color_palette)
                colors.append(self.color_palette[hash_val])
            
            return np.array(colors)
            
        except Exception as e:
            logger.error(f"Positional color generation failed: {e}")
            return np.full((len(vertices), 3), 0.5)

    def quantize_to_palette(self, colors: np.ndarray) -> np.ndarray:
        """Quantize colors to predefined palette"""
        try:
            quantized_colors = []
            for color in colors:
                distances = np.linalg.norm(self.color_palette - color, axis=1)
                closest_idx = np.argmin(distances)
                quantized_colors.append(self.color_palette[closest_idx])
            
            return np.array(quantized_colors)
            
        except Exception as e:
            logger.error(f"Color quantization failed: {e}")
            return colors

    def apply_lighting_enhancement(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Apply subtle lighting-based color enhancement"""
        try:
            if mesh.visual.vertex_colors is None:
                return mesh

            vertex_normals = mesh.vertex_normals
            light_direction = np.array([0, 0, 1])
            
            lighting = np.dot(vertex_normals, light_direction)
            lighting = np.clip(lighting, 0.3, 1.0)
            
            colors = mesh.visual.vertex_colors[:, :3].astype(float) / 255.0
            lit_colors = colors * lighting.reshape(-1, 1)
            lit_colors = np.clip(lit_colors, 0, 1)
            
            mesh.visual.vertex_colors = (lit_colors * 255).astype(np.uint8)
            
            logger.info("Lighting enhancement applied")
            return mesh
            
        except Exception as e:
            logger.error(f"Lighting enhancement failed: {e}")
            return mesh