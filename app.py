import streamlit as st
import base64
from PIL import Image
import io
import json

st.set_page_config(page_title="Collage Viewer", layout="wide")


def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def build_images_data(uploaded_files):
    images_data = []
    for uploaded_file in uploaded_files:
        try:
            image = Image.open(uploaded_file)
            max_size = (600, 600)
            image.thumbnail(max_size)

            img_b64 = image_to_base64(image)

            images_data.append({
                "src": f"data:image/png;base64,{img_b64}",
            })
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")

    return images_data


st.title("Infinite Collage Viewer")
st.markdown(
    "Upload images to see a dense, sliding infinite collage! "
    "Use the top layer uploader for images that should always appear above the others. "
    "Click anywhere to toggle fullscreen."
)

base_col, top_col = st.columns(2)

with base_col:
    uploaded_files = st.file_uploader(
        "Other layers",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        key="base_layers",
    )

with top_col:
    top_layer_files = st.file_uploader(
        "Top layer",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        key="top_layer",
    )

images_data = []
base_images_data = build_images_data(uploaded_files or [])
top_images_data = build_images_data(top_layer_files or [])
images_data.extend(base_images_data)
images_data.extend(top_images_data)

if images_data:
    base_images_json = json.dumps(base_images_data)
    top_images_json = json.dumps(top_images_data)

    html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Collage Viewer</title>
            <style>
                body {{ 
                    margin: 0; 
                    overflow: hidden; 
                    background-color: #000; 
                    height: 100vh;
                    width: 100vw;
                }}
                #marquee-container {{
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    position: relative;
                }}
                #marquee-track {{
                    display: flex;
                    width: 200vw; /* Two blocks of 100vw */
                    height: 100%;
                    animation: scroll 60s linear infinite;
                }}
                .collage-block {{
                    width: 100vw;
                    height: 100%;
                    position: relative;
                    flex-shrink: 0;
                }}
                .collage-img {{
                    position: absolute;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.8);
                    border: 3px solid white;
                    transition: transform 0.3s ease, z-index 0.3s;
                    max-width: 350px;
                    max-height: 350px;
                }}
                /* Hover effect removed as requested */
                @keyframes scroll {{
                    0% {{ transform: translateX(0); }}
                    100% {{ transform: translateX(-50%); }} /* Move half of 200vw */
                }}
            </style>
        </head>
        <body>
            <div id="marquee-container">
                <div id="marquee-track"></div>
            </div>
            <script>
                const baseImages = {base_images_json};
                const topImages = {top_images_json};
                const track = document.getElementById('marquee-track');

                // Function to create a block of images
                function createCollageBlock() {{
                    const block = document.createElement('div');
                    block.className = 'collage-block';

                    // Grid Configuration
                    // We want to cover 100vw x 100vh
                    // Let's use a grid that ensures coverage but minimizes heavy overlap
                    const cols = 10; 
                    const rows = 6;
                    const totalSlots = cols * rows;
                    const reservedTopSlots = topImages.length > 0 ? 10 : 0;
                    const cellWidth = 100 / cols; // %
                    const cellHeight = 100 / rows; // %
                    const slotLayers = Array(totalSlots).fill('base');

                    if (reservedTopSlots > 0) {{
                        for (let i = 0; i < reservedTopSlots; i++) {{
                            const slotIndex = Math.floor((i + 0.5) * totalSlots / reservedTopSlots);
                            slotLayers[slotIndex] = 'top';
                        }}
                    }}

                    let baseImgIndex = 0;
                    let topImgIndex = 0;

                    for (let r = 0; r < rows; r++) {{
                        for (let c = 0; c < cols; c++) {{
                            const slotIndex = (r * cols) + c;
                            const isTopSlot = slotLayers[slotIndex] === 'top';
                            const sourceImages = isTopSlot ? topImages : baseImages;
                            const fallbackImages = isTopSlot ? baseImages : topImages;

                            if (sourceImages.length === 0 && fallbackImages.length === 0) {{
                                continue;
                            }}

                            const imgData = sourceImages.length > 0
                                ? sourceImages[(isTopSlot ? topImgIndex++ : baseImgIndex++) % sourceImages.length]
                                : fallbackImages[(isTopSlot ? baseImgIndex++ : topImgIndex++) % fallbackImages.length];

                            const img = document.createElement('img');
                            img.src = imgData.src;
                            img.className = 'collage-img';

                            // Random Parameters
                            const rotate = Math.random() * 30 - 15; // -15 to 15 deg
                            // Scale needs to be large enough to cover gaps
                            // Cell size is approx 10% width. 
                            // We want image to be slightly larger than cell.
                            const scale = Math.random() * 0.4 + 1.1; // 1.1 to 1.5 relative to base size?
                            // Wait, CSS scale is relative to element size.
                            // We should set element size to match cell size roughly?
                            // Or just rely on max-width/height and scale?
                            // Let's set width to cellWidth * 1.5 in CSS or inline?
                            // Better to set base width in % to match grid.
                            img.style.width = (cellWidth * 1.4) + 'vw';
                            img.style.height = 'auto'; // Maintain aspect ratio
                            // But if aspect ratio is tall, it might not cover width.
                            // Let's use object-fit if we forced size, but we are using img tags.
                            // Let's just set a min-width to ensure coverage?
                            // Or just use a generous width.

                            const zIndexBase = isTopSlot ? 1001 : 1;
                            const zIndex = zIndexBase + Math.floor(Math.random() * 100);
                            
                            // Position: Center of cell + Jitter
                            // Jitter range: +/- 30% of cell size
                            const jitterX = (Math.random() - 0.5) * cellWidth * 0.6;
                            const jitterY = (Math.random() - 0.5) * cellHeight * 0.6;

                            const top = (r * cellHeight) + (cellHeight / 2) + jitterY;
                            const left = (c * cellWidth) + (cellWidth / 2) + jitterX;

                            img.style.top = top + '%';
                            img.style.left = left + '%';
                            // Use CSS scale for the "random size" feel
                            img.style.transform = `translate(-50%, -50%) rotate(${{rotate}}deg) scale(${{scale}})`;
                            img.style.zIndex = zIndex;

                            block.appendChild(img);
                        }}
                    }}
                    return block;
                }}

                // Create two identical blocks for seamless looping
                // Note: We need to ensure the random seed is "consistent" visually if we want perfect loop,
                // but since we are generating DOM elements, we can just generate two blocks.
                // However, for a perfect loop, the second block must look EXACTLY like the first one?
                // Actually, standard marquee technique uses two identical copies of content.
                // So we generate one block's content, then clone it.
                
                const block1 = createCollageBlock();
                const block2 = block1.cloneNode(true); // Deep clone to ensure identical layout

                track.appendChild(block1);
                track.appendChild(block2);

                // Fullscreen Toggle
                document.body.addEventListener('click', () => {{
                    if (!document.fullscreenElement) {{
                        document.body.requestFullscreen().catch(err => {{
                            console.log(`Error attempting to enable full-screen mode: ${{err.message}} ({{err.name}})`);
                        }});
                    }} else {{
                        document.exitFullscreen();
                    }}
                }});
            </script>
        </body>
        </html>
        """

    st.components.v1.html(html_code, height=800, scrolling=False)

else:
    st.info("Please upload image files to start.")
