"""3D mesh generation using Shap-E."""

import os
import torch
import logging
import trimesh
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class ShapEGenerator:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.models_loaded = False
        self.xm = None
        self.text_model = None
        self.diffusion = None
        
        logger.info(f"Using device: {self.device}")
        
    def load_models(self):
        """Load Shap-E models"""
        if self.models_loaded:
            return True
            
        try:
            logger.info("Loading Shap-E models...")
            
            from shap_e.diffusion.sample import sample_latents
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            from shap_e.models.download import load_model, load_config
            from shap_e.util.notebooks import decode_latent_mesh
            
            self.sample_latents = sample_latents
            self.diffusion_from_config = diffusion_from_config
            self.decode_latent_mesh = decode_latent_mesh
            
            self.xm = load_model('transmitter', device=self.device)
            self.text_model = load_model('text300M', device=self.device)
            self.diffusion = diffusion_from_config(load_config('diffusion'))
            
            self.models_loaded = True
            logger.info("Models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
    
    def enhance_prompt(self, prompt: str) -> str:
        """Advanced prompt engineering for 3D generation"""
        prompt = prompt.strip()
        
        category = self.detect_object_category(prompt)
        enhanced = self.apply_category_enhancements(prompt, category)
        enhanced = self.add_technical_specifications(enhanced)
        enhanced = self.add_quality_modifiers(enhanced)
        
        logger.info(f"Enhanced prompt: {enhanced}")
        return enhanced
    
    def detect_object_category(self, prompt: str) -> str:
        """Detect object type from prompt"""
        prompt_lower = prompt.lower()
        
        categories = {
            'weapon': ['sword', 'knife', 'gun', 'blade', 'axe', 'spear', 'bow', 'rifle', 'pistol'],
            'vehicle': ['car', 'truck', 'bike', 'motorcycle', 'plane', 'boat', 'ship', 'aircraft'],
            'furniture': ['chair', 'table', 'desk', 'bed', 'sofa', 'cabinet', 'shelf', 'stool'],
            'creature': ['dragon', 'monster', 'animal', 'beast', 'bird', 'fish', 'cat', 'dog'],
            'architecture': ['building', 'house', 'tower', 'castle', 'bridge', 'pillar', 'arch'],
            'tool': ['hammer', 'wrench', 'screwdriver', 'drill', 'saw', 'pliers', 'key'],
            'jewelry': ['ring', 'necklace', 'crown', 'bracelet', 'earring', 'pendant'],
            'food': ['apple', 'cake', 'bread', 'pizza', 'burger', 'fruit', 'vegetable'],
            'nature': ['tree', 'flower', 'rock', 'mountain', 'crystal', 'gem', 'stone'],
            'electronic': ['phone', 'computer', 'robot', 'device', 'gadget', 'machine']
        }
        
        for category, keywords in categories.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return category
        
        return 'generic'
    
    def apply_category_enhancements(self, prompt: str, category: str) -> str:
        """Apply category-specific prompt improvements"""
        
        enhancements = {
            'weapon': [
                "sharp detailed blade geometry",
                "realistic proportions and weight distribution",
                "defined edge topology",
                "functional grip design"
            ],
            'vehicle': [
                "aerodynamic body design",
                "realistic wheels and mechanical details",
                "proper scale and proportions",
                "functional automotive features"
            ],
            'furniture': [
                "ergonomic proportions",
                "realistic wood grain texture",
                "proper joint construction",
                "functional design elements"
            ],
            'creature': [
                "organic anatomical structure",
                "natural pose and proportions",
                "detailed surface features",
                "lifelike characteristics"
            ],
            'architecture': [
                "structural engineering accuracy",
                "realistic material textures",
                "proper architectural proportions",
                "detailed construction elements"
            ],
            'tool': [
                "functional mechanical design",
                "ergonomic handle construction",
                "realistic material properties",
                "proper tool proportions"
            ],
            'jewelry': [
                "intricate decorative details",
                "precious metal finish",
                "refined craftsmanship",
                "elegant proportions"
            ],
            'food': [
                "realistic organic texture",
                "natural color variation",
                "appetizing appearance",
                "proper food proportions"
            ],
            'nature': [
                "organic natural forms",
                "realistic surface textures",
                "natural color patterns",
                "environmentally appropriate"
            ],
            'electronic': [
                "sleek modern design",
                "functional button placement",
                "technological appearance",
                "precise geometric forms"
            ],
            'generic': [
                "well-defined geometry",
                "realistic proportions",
                "detailed surface features",
                "clean topology"
            ]
        }
        
        category_terms = enhancements.get(category, enhancements['generic'])
        selected_terms = np.random.choice(category_terms, size=2, replace=False)
        
        return f"{prompt}, {', '.join(selected_terms)}"
    
    def add_technical_specifications(self, prompt: str) -> str:
        """Add 3D-specific technical terms"""
        
        tech_specs = [
            "high-quality 3D mesh",
            "clean topology",
            "well-defined vertices",
            "optimized polygon count",
            "manifold geometry",
            "proper UV mapping ready",
            "game-asset quality"
        ]
        
        selected_specs = np.random.choice(tech_specs, size=2, replace=False)
        
        return f"{prompt}, {', '.join(selected_specs)}"
    
    def add_quality_modifiers(self, prompt: str) -> str:
        """Add quality and style modifiers"""
        
        quality_terms = [
            "highly detailed",
            "professional quality",
            "studio-grade model",
            "production-ready asset",
            "crisp clean design",
            "precise manufacturing",
            "expert craftsmanship"
        ]
        
        style_terms = [
            "realistic rendering",
            "contemporary design",
            "modern aesthetic",
            "sleek appearance",
            "refined details",
            "sophisticated finish"
        ]
        
        quality = np.random.choice(quality_terms)
        style = np.random.choice(style_terms)
        
        return f"{prompt}, {quality}, {style}, 3D model"
    
    def generate_from_text(self, prompt: str, steps: int = 128, guidance_scale: float = 25.0) -> Optional[trimesh.Trimesh]:
        """Generate 3D mesh from text prompt"""
        if not self.load_models():
            return None
        
        try:
            enhanced_prompt = self.enhance_prompt(prompt)
            logger.info("Generating 3D model...")
            
            batch_size = 1
            latents = self.sample_latents(
                batch_size=batch_size,
                model=self.text_model,
                diffusion=self.diffusion,
                guidance_scale=guidance_scale,
                model_kwargs=dict(texts=[enhanced_prompt] * batch_size),
                progress=True,
                clip_denoised=True,
                use_fp16=True,
                use_karras=True,
                karras_steps=steps,
                sigma_min=1e-4,
                sigma_max=80,
                s_churn=0,
            )
            
            logger.info("Decoding latent to mesh...")
            mesh_obj = self.decode_latent_mesh(self.xm, latents[0]).tri_mesh()
            
            vertices = mesh_obj.verts
            faces = mesh_obj.faces
            
            # Extract vertex colors
            vertex_colors = None
            try:
                if hasattr(mesh_obj, 'vertex_channels'):
                    channels = mesh_obj.vertex_channels
                    if channels and 'R' in channels:
                        r = channels['R']
                        g = channels['G']
                        b = channels['B']
                        
                        vertex_colors = np.column_stack([r, g, b])
                        vertex_colors = np.clip(vertex_colors, 0, 1)
                        logger.info("Extracted vertex colors")
            except Exception as e:
                logger.warning(f"Could not extract colors: {e}")
            
            mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=faces,
                vertex_colors=vertex_colors
            )
            
            logger.info(f"Generated mesh: {len(vertices)} vertices, {len(faces)} faces")
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return mesh
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return None