import streamlit as st
import base64
from PIL import Image
import io
import json

st.set_page_config(page_title="Floating Images 3D Viewer", layout="wide")

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

st.title("Floating Images 3D Viewer")
st.markdown("Upload images to see them float in space! Click anywhere on the 3D view to toggle fullscreen.")

uploaded_files = st.file_uploader("Choose images", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if uploaded_files:
    images_data = []
    for uploaded_file in uploaded_files:
        try:
            image = Image.open(uploaded_file)
            # Resize if too large to prevent performance issues/huge base64 strings
            max_size = (800, 800)
            image.thumbnail(max_size)
            
            img_b64 = image_to_base64(image)
            width, height = image.size
            aspect_ratio = width / height
            
            images_data.append({
                "src": f"data:image/png;base64,{img_b64}",
                "aspect": aspect_ratio
            })
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")

    if images_data:
        # Serialize data for JS
        images_json = json.dumps(images_data)

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Three.js Viewer</title>
            <style>
                body {{ margin: 0; overflow: hidden; background-color: #000; }}
                canvas {{ display: block; }}
            </style>
        </head>
        <body>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script>
                const images = {images_json};

                // Scene setup
                const scene = new THREE.Scene();
                // scene.background = new THREE.Color(0x000000); // CSS handles background

                const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.z = 12; // Moved back slightly to see the circle better
                camera.position.y = 2;
                camera.lookAt(0, 0, 0);

                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);

                // Starfield Background
                const starGeometry = new THREE.BufferGeometry();
                const starCount = 2000;
                const starPositions = new Float32Array(starCount * 3);
                for(let i=0; i<starCount*3; i++) {{
                    starPositions[i] = (Math.random() - 0.5) * 100;
                }}
                starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
                const starMaterial = new THREE.PointsMaterial({{ color: 0xffffff, size: 0.1, transparent: true, opacity: 0.8 }});
                const stars = new THREE.Points(starGeometry, starMaterial);
                scene.add(stars);

                // Objects
                const meshes = [];
                const radius = 8; // Radius of the circle
                
                images.forEach((imgData, index) => {{
                    const loader = new THREE.TextureLoader();
                    loader.load(imgData.src, (texture) => {{
                        // Adjust plane size based on aspect ratio
                        const baseHeight = 2.0;
                        const geometry = new THREE.PlaneGeometry(baseHeight * imgData.aspect, baseHeight);
                        const material = new THREE.MeshBasicMaterial({{ 
                            map: texture, 
                            side: THREE.DoubleSide,
                            transparent: true 
                        }});
                        const plane = new THREE.Mesh(geometry, material);

                        // Initial Position (Circular distribution)
                        const angle = (index / images.length) * Math.PI * 2;
                        plane.position.x = Math.cos(angle) * radius;
                        plane.position.z = Math.sin(angle) * radius;
                        plane.position.y = (Math.random() - 0.5) * 4;

                        // Store animation data
                        plane.userData = {{
                            initialY: plane.position.y,
                            angle: angle,
                            speed: 0.005, // Orbital speed
                            floatSpeed: 0.002 + Math.random() * 0.003,
                            phase: Math.random() * Math.PI * 2
                        }};

                        scene.add(plane);
                        meshes.push(plane);
                    }});
                }});

                // Animation
                function animate() {{
                    requestAnimationFrame(animate);

                    const time = Date.now();

                    // Animate Stars
                    stars.rotation.y += 0.0002;

                    meshes.forEach(mesh => {{
                        // Orbital movement
                        mesh.userData.angle += mesh.userData.speed;
                        mesh.position.x = Math.cos(mesh.userData.angle) * radius;
                        mesh.position.z = Math.sin(mesh.userData.angle) * radius;

                        // Floating effect (Y axis)
                        mesh.position.y = mesh.userData.initialY + Math.sin(time * mesh.userData.floatSpeed + mesh.userData.phase) * 0.5;

                        // Billboarding: Always face the camera
                        mesh.lookAt(camera.position);
                    }});

                    renderer.render(scene, camera);
                }}

                animate();

                // Handle Click for Fullscreen
                document.body.addEventListener('click', () => {{
                    if (!document.fullscreenElement) {{
                        document.body.requestFullscreen().catch(err => {{
                            console.log(`Error attempting to enable full-screen mode: ${{err.message}} ({{err.name}})`);
                        }});
                    }} else {{
                        document.exitFullscreen();
                    }}
                }});

                // Handle Resize
                window.addEventListener('resize', () => {{
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                }});
            </script>
        </body>
        </html>
        """

        st.components.v1.html(html_code, height=600, scrolling=False)

else:
    st.info("Please upload image files to start.")
