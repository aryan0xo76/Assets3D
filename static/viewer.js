/**
 * VoxelForge 3D Viewer - Three.js Implementation
 */

class VoxelForgeViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.currentMesh = null;
    this.lights = [];
    this.wireframeMode = false;
    this.backgroundColor = 0x667eea;

    this.init();
  }

  init() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.backgroundColor);

    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
    this.camera.position.set(2, 2, 2);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });
    this.renderer.setSize(
      this.container.clientWidth,
      this.container.clientHeight
    );
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.container.appendChild(this.renderer.domElement);

    this.controls = new THREE.OrbitControls(
      this.camera,
      this.renderer.domElement
    );
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.1;
    this.controls.enableZoom = true;
    this.controls.enablePan = true;
    this.controls.enableRotate = true;

    this.setupLighting();

    window.addEventListener("resize", () => this.onWindowResize());

    this.animate();

    console.log("VoxelForge 3D Viewer initialized");
  }

  setupLighting() {
    // Clear existing lights
    this.lights.forEach((light) => this.scene.remove(light));
    this.lights = [];

    // Higher ambient light for even base illumination
    const ambientLight = new THREE.AmbientLight(0x606060, 0.7);
    this.scene.add(ambientLight);
    this.lights.push(ambientLight);

    // Main directional light (reduced intensity)
    const mainLight = new THREE.DirectionalLight(0xffffff, 0.4);
    mainLight.position.set(5, 5, 5);
    mainLight.castShadow = false; // Disable harsh shadows
    this.scene.add(mainLight);
    this.lights.push(mainLight);

    // Strong fill light from opposite side
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight.position.set(-5, 3, -5);
    this.scene.add(fillLight);
    this.lights.push(fillLight);

    // Top light for even coverage
    const topLight = new THREE.DirectionalLight(0xffffff, 0.3);
    topLight.position.set(0, 8, 0);
    this.scene.add(topLight);
    this.lights.push(topLight);

    // Side lights for complete coverage
    const sideLight1 = new THREE.DirectionalLight(0xffffff, 0.2);
    sideLight1.position.set(8, 0, 0);
    this.scene.add(sideLight1);
    this.lights.push(sideLight1);

    const sideLight2 = new THREE.DirectionalLight(0xffffff, 0.2);
    sideLight2.position.set(-8, 0, 0);
    this.scene.add(sideLight2);
    this.lights.push(sideLight2);
  }

  loadPLY(filename, onProgress = null, onComplete = null) {
    console.log(`Loading PLY file: ${filename}`);

    this.showLoading(true);

    if (this.currentMesh) {
      this.scene.remove(this.currentMesh);
      this.currentMesh = null;
    }

    const loader = new THREE.PLYLoader();

    loader.load(
      `/download/${filename}`,
      (geometry) => {
        console.log("PLY file loaded successfully");
        this.onPLYLoaded(geometry, filename);
        if (onComplete) onComplete();
      },
      (progress) => {
        if (onProgress) onProgress(progress);
      },
      (error) => {
        console.error("Failed to load PLY file:", error);
        this.showError("Failed to load 3D model");
        this.showLoading(false);
      }
    );
  }

  onPLYLoaded(geometry, filename) {
    try {
      console.log(`Geometry info:`, {
        vertices: geometry.attributes.position.count,
        hasColors: !!geometry.attributes.color,
        hasNormals: !!geometry.attributes.normal,
      });

      if (!geometry.attributes.normal) {
        geometry.computeVertexNormals();
      }

      geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);

      geometry.translate(-center.x, -center.y, -center.z);

      if (maxDim > 0) {
        geometry.scale(2 / maxDim, 2 / maxDim, 2 / maxDim);
      }

      // Simple material for full RGB spectrum colors
      const material = new THREE.MeshStandardMaterial({
        vertexColors: geometry.attributes.color ? true : false,
        color: geometry.attributes.color ? 0xffffff : 0x888888,
        roughness: 0.6,
        metalness: 0.2,
        side: THREE.FrontSide,
        wireframe: this.wireframeMode,
      });

      this.currentMesh = new THREE.Mesh(geometry, material);
      this.currentMesh.castShadow = true;
      this.currentMesh.receiveShadow = true;

      this.scene.add(this.currentMesh);

      this.resetCamera();

      this.updateModelInfo({
        vertices: geometry.attributes.position.count,
        faces: geometry.index ? geometry.index.count / 3 : 0,
        filename: filename,
      });

      this.showLoading(false);
      this.hideMessage();

      console.log("3D model displayed successfully");
    } catch (error) {
      console.error("Error processing PLY geometry:", error);
      this.showError("Error processing 3D model");
      this.showLoading(false);
    }
  }

  toggleWireframe() {
    this.wireframeMode = !this.wireframeMode;

    if (this.currentMesh && this.currentMesh.material) {
      this.currentMesh.material.wireframe = this.wireframeMode;
    }

    const btn = document.getElementById("wireframeBtn");
    if (btn) {
      btn.classList.toggle("active", this.wireframeMode);
      btn.textContent = this.wireframeMode ? "Solid" : "Wireframe";
    }

    console.log(`Wireframe mode: ${this.wireframeMode ? "ON" : "OFF"}`);
  }

  resetCamera() {
    if (this.currentMesh) {
      this.camera.position.set(3, 2, 3);
      this.camera.lookAt(0, 0, 0);
      this.controls.target.set(0, 0, 0);
    } else {
      this.camera.position.set(2, 2, 2);
      this.camera.lookAt(0, 0, 0);
      this.controls.target.set(0, 0, 0);
    }

    this.controls.update();
    console.log("Camera reset");
  }

  toggleBackground() {
    const colors = [0x667eea, 0x2c3e50, 0xffffff, 0x000000, 0x34495e];
    const currentIndex = colors.indexOf(this.backgroundColor);
    const nextIndex = (currentIndex + 1) % colors.length;

    this.backgroundColor = colors[nextIndex];
    this.scene.background = new THREE.Color(this.backgroundColor);

    console.log(
      `Background color changed to: #${this.backgroundColor.toString(16)}`
    );
  }

  showLoading(show) {
    const overlay = document.getElementById("loadingOverlay");
    if (overlay) {
      overlay.style.display = show ? "flex" : "none";
    }
  }

  showMessage(html) {
    const message = document.getElementById("viewer-message");
    if (message) {
      message.innerHTML = html;
      message.style.display = "flex";
    }
  }

  hideMessage() {
    const message = document.getElementById("viewer-message");
    if (message) {
      message.style.display = "none";
    }
  }

  showError(errorText) {
    const html = `
            <div class="viewer-placeholder">
                <div class="placeholder-icon">⚠</div>
                <h3>Error Loading Model</h3>
                <p>${errorText}</p>
            </div>
        `;
    this.showMessage(html);
  }

  updateModelInfo(info) {
    const modelInfo = document.getElementById("modelInfo");
    const vertexCount = document.getElementById("vertexCount");
    const faceCount = document.getElementById("faceCount");

    if (vertexCount)
      vertexCount.textContent = `Vertices: ${info.vertices.toLocaleString()}`;
    if (faceCount)
      faceCount.textContent = `Faces: ${info.faces.toLocaleString()}`;

    if (modelInfo) {
      modelInfo.style.display = "block";
    }

    console.log("Model info updated:", info);
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);

    console.log(`Viewer resized: ${width}x${height}`);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    if (this.renderer) {
      this.renderer.dispose();
    }

    if (this.currentMesh) {
      this.scene.remove(this.currentMesh);
    }

    console.log("Viewer disposed");
  }
}

// Global viewer instance
let viewer = null;

// Initialize viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        viewer = new VoxelForgeViewer('viewer-canvas');
        console.log('3D Viewer ready');
    } catch (error) {
        console.error('Failed to initialize viewer:', error);
    }
});

// Global functions for HTML button events
function toggleWireframe() {
    if (viewer) viewer.toggleWireframe();
}

function resetCamera() {
    if (viewer) viewer.resetCamera();
}

function toggleBackground() {
    if (viewer) viewer.toggleBackground();
}