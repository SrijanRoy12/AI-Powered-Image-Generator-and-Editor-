import streamlit as st
import os
from dotenv import load_dotenv
from services import (
    lifestyle_shot_by_image,
    lifestyle_shot_by_text,
    add_shadow,
    create_packshot,
    enhance_prompt,
    generative_fill,
    generate_hd_image,
    erase_foreground
)
from PIL import Image
import io
import requests
import json
import time
import base64
from streamlit_drawable_canvas import st_canvas
import numpy as np
from services.erase_foreground import erase_foreground

# Configure Streamlit page with enhanced layout
st.set_page_config(
    page_title="DreamPixel AI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.pixeloom.ai/help',
        'Report a bug': "https://www.pixeloom.ai/bug",
        'About': "# DreamPixel AI Studio\n### The ultimate AI-powered image generation and editing suite"
    }
)

# Custom CSS for improved styling
st.markdown("""
<style>
    /* Main headers */
    .stApp header h1 {
        font-size: 2.5rem !important;
        color: #4a4a4a !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 25px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0 !important;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e1e4eb;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #4a4a4a !important;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #d1d5db !important;
        border-radius: 10px !important;
        padding: 20px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* Cards for features */
    .feature-card {
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #6366f1 !important;
    }
    
    /* Custom columns */
    .custom-col {
        padding: 15px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    
    /* Tooltips */
    .stTooltip {
        font-size: 0.9rem !important;
    }
    
    /* Success messages */
    .stAlert [data-testid="stMarkdownContainer"] {
        font-size: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
print("Loading environment variables...")
load_dotenv(verbose=True)

def initialize_session_state():
    """Initialize session state variables with improved structure."""
    defaults = {
        'api_key': os.getenv('BRIA_API_KEY'),
        'generated_images': [],
        'current_image': None,
        'pending_urls': [],
        'edited_image': None,
        'original_prompt': "",
        'enhanced_prompt': None,
        'active_tab': "🎨 Generate Image",
        'last_action': None,
        'history': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def download_image(url):
    """Download image from URL with enhanced error handling."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"🚨 Error downloading image: {str(e)}")
        return None

def create_feature_card(title, description, icon="✨"):
    """Create a consistent feature card UI element."""
    with st.container():
        st.markdown(f"""
        <div class="feature-card">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
        </div>
        """, unsafe_allow_html=True)

def show_image_editor(image, key_suffix=""):
    """Enhanced image editor with more options."""
    with st.expander("🖼️ Image Editor", expanded=True):
        cols = st.columns([1, 1, 1, 1])
        
        with cols[0]:
            filter_type = st.selectbox(
                "Select Filter", 
                ["None", "Grayscale", "Sepia", "High Contrast", "Blur"],
                key=f"filter_{key_suffix}"
            )
            
        with cols[1]:
            brightness = st.slider(
                "Brightness", 
                min_value=0.5, 
                max_value=1.5, 
                value=1.0, 
                step=0.1,
                key=f"brightness_{key_suffix}"
            )
            
        with cols[2]:
            contrast = st.slider(
                "Contrast", 
                min_value=0.5, 
                max_value=1.5, 
                value=1.0, 
                step=0.1,
                key=f"contrast_{key_suffix}"
            )
            
        with cols[3]:
            saturation = st.slider(
                "Saturation", 
                min_value=0.0, 
                max_value=2.0, 
                value=1.0, 
                step=0.1,
                key=f"saturation_{key_suffix}"
            )
        
        # Apply filters
        try:
            img = Image.open(io.BytesIO(image)) if isinstance(image, bytes) else image
            
            if filter_type != "None":
                if filter_type == "Grayscale":
                    img = img.convert('L')
                elif filter_type == "Sepia":
                    width, height = img.size
                    pixels = img.load()
                    for x in range(width):
                        for y in range(height):
                            r, g, b = img.getpixel((x, y))[:3]
                            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                            img.putpixel((x, y), (min(tr, 255), min(tg, 255), min(tb, 255)))
                elif filter_type == "High Contrast":
                    img = img.point(lambda x: x * 1.5)
                elif filter_type == "Blur":
                    img = img.filter(Image.BLUR)
            
            # Apply other adjustments
            # (Implementation would go here)
            
            return img
        except Exception as e:
            st.error(f"Error applying filters: {str(e)}")
            return image

def main():
    # Initialize session state
    initialize_session_state()
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("DreamPixe AI Studio")
        st.markdown("""
        <div style="font-size: 1.2rem; color: #4a4a4a; margin-bottom: 2rem;">
            Transform your creative workflow with AI-powered image generation and editing.
            Create stunning visuals in seconds with our advanced tools.
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.metric("Generations", "10K+", "↑ 12%")
        with stats_cols[1]:
            st.metric("Active Users", "5K+", "↑ 8%")
        with stats_cols[2]:
            st.metric("Features", "15+", "New!")
        with stats_cols[3]:
            st.metric("Satisfaction", "98%", "↑ 2%")
    
    with col2:
        # Placeholder for a sample generated image
        st.image("https://via.placeholder.com/400x250?text=Sample+AI+Creation", 
                caption="Sample AI-Generated Image", use_column_width=True)
    
    # Sidebar with improved layout
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #4a4a4a;">Pixeloom AI</h2>
            <p style="color: #6b7280;">Version 2.1</p>
        </div>
        """, unsafe_allow_html=True)
        
        # API Key section
        with st.expander("🔑 API Settings", expanded=True):
            api_key = st.text_input(
                "Enter your API key:", 
                value=st.session_state.api_key if st.session_state.api_key else "", 
                type="password",
                help="Get your API key from the Pixeloom dashboard"
            )
            if api_key:
                st.session_state.api_key = api_key
                st.success("API key saved!")
            
            st.markdown("[Get an API key](https://api.pixeloom.ai)")
        
        # Quick Actions
        with st.expander("⚡ Quick Actions", expanded=True):
            if st.button("🔄 Clear All", help="Reset the entire workspace"):
                for key in list(st.session_state.keys()):
                    if key not in ['api_key']:
                        del st.session_state[key]
                st.success("Workspace cleared!")
                st.experimental_rerun()
            
            if st.button("📋 Copy Last Prompt", help="Copy the last used prompt to clipboard"):
                if st.session_state.get('original_prompt'):
                    st.session_state.copied_prompt = st.session_state.original_prompt
                    st.success("Prompt copied!")
                else:
                    st.warning("No prompt available to copy")
        
        # Recent History
        if st.session_state.get('history'):
            with st.expander("🕒 Recent Actions", expanded=True):
                for action in reversed(st.session_state.history[-3:]):
                    st.caption(f"• {action}")
    
    # Main tabs with enhanced UI
    tab_labels = [
        "🎨 Generate Image", 
        "🖼️ Lifestyle Shot", 
        "🖌️ Generative Fill", 
        "🧹 Erase Elements",
        "⚙️ Settings"
    ]
    
    tabs = st.tabs(tab_labels)
    
    # Generate Images Tab - Enhanced
    with tabs[0]:
        st.header("AI Image Generation")
        st.markdown("Create stunning images from text prompts with our advanced AI models.")
        
        # Feature cards
        create_feature_card(
            "Prompt Enhancement", 
            "Get AI suggestions to improve your prompts for better results",
            "✨"
        )
        
        cols = st.columns([3, 1])
        with cols[0]:
            # Enhanced prompt input with examples
            with st.container():
                prompt = st.text_area(
                    "Describe what you want to create...", 
                    height=150,
                    placeholder="e.g., 'A futuristic cityscape at sunset with flying cars and neon lights'",
                    key="prompt_input_gen"
                )
                
                # Example prompts
                with st.expander("💡 Need inspiration? Try these examples"):
                    ex_cols = st.columns(2)
                    with ex_cols[0]:
                        if st.button("Majestic mountain landscape"):
                            st.session_state.prompt_input_gen = "A majestic mountain landscape at sunrise with a crystal-clear lake in the foreground, photorealistic 8K"
                    with ex_cols[1]:
                        if st.button("Cyberpunk street scene"):
                            st.session_state.prompt_input_gen = "A crowded cyberpunk street at night with neon signs, rain-soaked pavement, and futuristic vehicles, cinematic lighting"
                
                # Store original prompt
                if prompt and prompt != st.session_state.get('original_prompt_gen'):
                    st.session_state.original_prompt_gen = prompt
                    st.session_state.enhanced_prompt_gen = None
                
                # Enhanced prompt display
                if st.session_state.get('enhanced_prompt_gen'):
                    st.markdown("""
                    <div style="background-color: #f0f5ff; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <p style="margin: 0; font-weight: 600;">Enhanced Prompt:</p>
                        <p style="margin: 0; font-style: italic;">{}</p>
                    </div>
                    """.format(st.session_state.enhanced_prompt_gen), unsafe_allow_html=True)
            
            # Enhance Prompt button with loading state
            if st.button("✨ Enhance Prompt", key="enhance_button_gen"):
                if not prompt:
                    st.warning("Please enter a prompt to enhance")
                else:
                    with st.spinner("Analyzing your prompt..."):
                        try:
                            result = enhance_prompt(st.session_state.api_key, prompt)
                            if result:
                                st.session_state.enhanced_prompt_gen = result
                                st.session_state.history.append(f"Enhanced prompt: {prompt[:30]}...")
                                st.success("Prompt enhanced!")
                        except Exception as e:
                            st.error(f"Error enhancing prompt: {str(e)}")
        
        with cols[1]:
            # Generation settings in a card-like container
            with st.container():
                st.markdown("""
                <div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h4 style="margin-top: 0;">⚙️ Generation Settings</h4>
                """, unsafe_allow_html=True)
                
                num_images = st.slider("Number of images", 1, 4, 1, key="num_images_gen")
                aspect_ratio = st.selectbox("Aspect ratio", ["1:1", "16:9", "9:16", "4:3", "3:4"], key="aspect_gen")
                style = st.selectbox("Style", [
                    "Realistic", "Artistic", "Cartoon", "Sketch", 
                    "Watercolor", "Oil Painting", "Digital Art"
                ], key="style_gen")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Generate button with prominent styling
        if st.button("🚀 Generate Images", type="primary", key="generate_btn_main"):
            if not st.session_state.api_key:
                st.error("Please enter your API key in the sidebar")
                return
                
            if not prompt:
                st.warning("Please enter a prompt")
                return
                
            with st.spinner("🎨 Creating your masterpiece..."):
                try:
                    # Convert aspect ratio to proper format
                    result = generate_hd_image(
                        prompt=st.session_state.enhanced_prompt_gen or prompt,
                        api_key=st.session_state.api_key,
                        num_results=num_images,
                        aspect_ratio=aspect_ratio,
                        sync=True,
                        enhance_image=True,
                        medium="art" if style != "Realistic" else "photography",
                        content_moderation=True
                    )
                    
                    if result:
                        # Process results
                        if isinstance(result, dict):
                            if "result_url" in result:
                                st.session_state.edited_image = result["result_url"]
                                st.session_state.history.append(f"Generated image from prompt: {prompt[:30]}...")
                                st.success("✨ Image generated successfully!")
                            elif "result_urls" in result:
                                st.session_state.generated_images = result["result_urls"]
                                st.session_state.edited_image = result["result_urls"][0]
                                st.session_state.history.append(f"Generated {len(result['result_urls'])} images")
                                st.success(f"✨ {len(result['result_urls'])} images generated successfully!")
                        else:
                            st.error("Unexpected response format from API")
                            
                        # Display results
                        if st.session_state.get('generated_images'):
                            st.subheader("Generated Images")
                            img_cols = st.columns(min(4, len(st.session_state.generated_images)))
                            for idx, img_url in enumerate(st.session_state.generated_images[:4]):
                                with img_cols[idx]:
                                    st.image(img_url, use_column_width=True)
                                    img_data = download_image(img_url)
                                    if img_data:
                                        st.download_button(
                                            f"⬇️ Download #{idx+1}",
                                            img_data,
                                            f"generated_image_{idx+1}.png",
                                            "image/png",
                                            key=f"dl_gen_{idx}"
                                        )
                except Exception as e:
                    st.error(f"Error generating images: {str(e)}")
    
    # Product Photography Tab - Enhanced
    with tabs[1]:
        st.header("Professional Product Shots")
        st.markdown("Transform product images into professional lifestyle shots and packshots.")
        
        # Feature cards
        create_feature_card(
            "Background Removal", 
            "Automatically remove backgrounds from product images",
            "✂️"
        )
        create_feature_card(
            "Shadow Effects", 
            "Add realistic shadows to make products pop",
            "🌓"
        )
        
        # Main content
        uploaded_file = st.file_uploader(
            "Upload Product Image", 
            type=["png", "jpg", "jpeg"], 
            key="product_upload_v2",
            help="For best results, use high-quality images with clear product edges"
        )
        
        if uploaded_file:
            cols = st.columns([1, 1])
            with cols[0]:
                # Original image with editor
                st.subheader("Original Image")
                st.image(uploaded_file, use_column_width=True)
                
                # Editing options in an accordion
                edit_option = st.selectbox(
                    "Select Edit Option", 
                    ["Create Packshot", "Add Shadow", "Lifestyle Shot"],
                    key="edit_option_v2"
                )
                
                # Packshot options
                if edit_option == "Create Packshot":
                    with st.expander("📦 Packshot Settings", expanded=True):
                        bg_cols = st.columns(2)
                        with bg_cols[0]:
                            bg_color = st.color_picker("Background Color", "#FFFFFF")
                        with bg_cols[1]:
                            force_rmbg = st.toggle("Remove Background", True)
                        
                        sku = st.text_input("SKU (optional)", "")
                        content_moderation = st.toggle("Content Moderation", True)
                        
                        if st.button("🖼️ Create Packshot", key="packshot_btn"):
                            with st.spinner("Creating professional packshot..."):
                                try:
                                    result = create_packshot(
                                        st.session_state.api_key,
                                        uploaded_file.getvalue(),
                                        background_color=bg_color,
                                        sku=sku if sku else None,
                                        force_rmbg=force_rmbg,
                                        content_moderation=content_moderation
                                    )
                                    
                                    if result and "result_url" in result:
                                        st.session_state.edited_image = result["result_url"]
                                        st.session_state.history.append("Created packshot")
                                        st.success("✨ Packshot created successfully!")
                                except Exception as e:
                                    st.error(f"Error creating packshot: {str(e)}")
                
                # Shadow options
                elif edit_option == "Add Shadow":
                    with st.expander("🌓 Shadow Settings", expanded=True):
                        shadow_cols = st.columns(2)
                        with shadow_cols[0]:
                            shadow_type = st.selectbox("Type", ["Natural", "Drop", "Float"])
                            shadow_color = st.color_picker("Color", "#000000")
                        with shadow_cols[1]:
                            shadow_intensity = st.slider("Intensity", 0, 100, 60)
                            shadow_blur = st.slider("Blur", 0, 50, 15)
                        
                        offset_cols = st.columns(2)
                        with offset_cols[0]:
                            offset_x = st.slider("X Offset", -50, 50, 0)
                        with offset_cols[1]:
                            offset_y = st.slider("Y Offset", -50, 50, 15)
                        
                        if st.button("🌓 Add Shadow", key="shadow_btn"):
                            with st.spinner("Adding shadow effect..."):
                                try:
                                    result = add_shadow(
                                        api_key=st.session_state.api_key,
                                        image_data=uploaded_file.getvalue(),
                                        shadow_type=shadow_type.lower(),
                                        shadow_color=shadow_color,
                                        shadow_offset=[offset_x, offset_y],
                                        shadow_intensity=shadow_intensity,
                                        shadow_blur=shadow_blur
                                    )
                                    
                                    if result and "result_url" in result:
                                        st.session_state.edited_image = result["result_url"]
                                        st.session_state.history.append("Added shadow effect")
                                        st.success("✨ Shadow added successfully!")
                                except Exception as e:
                                    st.error(f"Error adding shadow: {str(e)}")
                
                # Lifestyle shot options
                elif edit_option == "Lifestyle Shot":
                    with st.expander("🌆 Lifestyle Settings", expanded=True):
                        shot_type = st.radio("Type", ["Text Prompt", "Reference Image"])
                        
                        if shot_type == "Text Prompt":
                            prompt = st.text_area("Describe the scene")
                            num_results = st.slider("Variations", 1, 4, 1)
                            
                            if st.button("🌆 Generate Lifestyle Shot", key="lifestyle_btn"):
                                if not prompt:
                                    st.warning("Please describe the scene")
                                else:
                                    with st.spinner("Creating lifestyle shot..."):
                                        try:
                                            result = lifestyle_shot_by_text(
                                                api_key=st.session_state.api_key,
                                                image_data=uploaded_file.getvalue(),
                                                scene_description=prompt,
                                                num_results=num_results,
                                                sync=True
                                            )
                                            
                                            if result:
                                                if "result_urls" in result:
                                                    st.session_state.generated_images = result["result_urls"]
                                                    st.session_state.edited_image = result["result_urls"][0]
                                                    st.session_state.history.append(f"Generated {len(result['result_urls'])} lifestyle shots")
                                                    st.success(f"✨ {len(result['result_urls'])} lifestyle shots created!")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                        else:
                            ref_image = st.file_uploader("Upload Reference Scene", type=["png", "jpg", "jpeg"])
                            ref_influence = st.slider("Reference Influence", 0.0, 1.0, 0.7)
                            
                            if st.button("🌆 Generate Lifestyle Shot", key="lifestyle_ref_btn") and ref_image:
                                with st.spinner("Creating lifestyle shot..."):
                                    try:
                                        result = lifestyle_shot_by_image(
                                            api_key=st.session_state.api_key,
                                            image_data=uploaded_file.getvalue(),
                                            reference_image=ref_image.getvalue(),
                                            ref_image_influence=ref_influence
                                        )
                                        
                                        if result and "result_url" in result:
                                            st.session_state.edited_image = result["result_url"]
                                            st.session_state.history.append("Created lifestyle shot from reference")
                                            st.success("✨ Lifestyle shot created successfully!")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            
            with cols[1]:
                # Results display
                st.subheader("Result")
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, use_column_width=True)
                    
                    # Download button
                    img_data = download_image(st.session_state.edited_image)
                    if img_data:
                        st.download_button(
                            "⬇️ Download Result",
                            img_data,
                            "result_image.png",
                            "image/png",
                            key="dl_result"
                        )
                    
                    # Variations if available
                    if st.session_state.get('generated_images') and len(st.session_state.generated_images) > 1:
                        st.subheader("Variations")
                        var_cols = st.columns(2)
                        for idx, img_url in enumerate(st.session_state.generated_images[1:3]):
                            with var_cols[idx % 2]:
                                st.image(img_url, use_column_width=True)
                                img_data = download_image(img_url)
                                if img_data:
                                    st.download_button(
                                        f"⬇️ Download Var {idx+1}",
                                        img_data,
                                        f"variation_{idx+1}.png",
                                        "image/png",
                                        key=f"dl_var_{idx}"
                                    )
                else:
                    st.info("👆 Generate an image to see results here")
    
    # Generative Fill Tab - Enhanced
    with tabs[2]:
        st.header("AI-Powered Generative Fill")
        st.markdown("Remove unwanted elements or add new ones with AI magic.")
        
        # Feature cards
        create_feature_card(
            "Smart Masking", 
            "Draw simple masks and let AI handle the complex inpainting",
            "🎭"
        )
        create_feature_card(
            "Context-Aware", 
            "AI understands the context of your image for seamless edits",
            "🧠"
        )
        
        # Main content
        uploaded_file = st.file_uploader(
            "Upload Image to Edit", 
            type=["png", "jpg", "jpeg"], 
            key="gen_fill_upload"
        )
        
        if uploaded_file:
            cols = st.columns([1, 1])
            
            with cols[0]:
                st.subheader("Original Image")
                img = Image.open(uploaded_file)
                
                # Calculate canvas dimensions
                width, height = img.size
                aspect_ratio = height / width
                canvas_width = min(width, 700)
                canvas_height = int(canvas_width * aspect_ratio)
                
                # Create drawing canvas
                st.markdown("**Draw on the image to create a mask**")
                stroke_width = st.slider("Brush Size", 1, 50, 20, key="brush_size_fill")
                
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",
                    stroke_width=stroke_width,
                    stroke_color="#FFFFFF",
                    background_image=img.resize((canvas_width, canvas_height)),
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="freedraw",
                    key="canvas_fill"
                )
                
                # Generation options
                with st.expander("⚙️ Generation Settings", expanded=True):
                    prompt = st.text_area(
                        "What should appear in the masked area?",
                        placeholder="e.g., 'a bowl of fruit on the table'"
                    )
                    
                    adv_cols = st.columns(2)
                    with adv_cols[0]:
                        negative_prompt = st.text_input(
                            "Exclude from generation (optional)",
                            placeholder="e.g., 'people, text, logos'"
                        )
                    with adv_cols[1]:
                        num_variations = st.slider("Variations", 1, 4, 1)
                
                if st.button("✨ Generate", type="primary", key="gen_fill_btn"):
                    if not prompt:
                        st.warning("Please describe what to generate")
                    elif canvas_result.image_data is None or not np.any(canvas_result.image_data[..., -1] > 0):
                        st.warning("Please draw a mask on the image first")
                    else:
                        with st.spinner("Generating content..."):
                            try:
                                # Prepare mask
                                mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), mode='RGBA')
                                mask_img = mask_img.convert('L')
                                mask_bytes = io.BytesIO()
                                mask_img.save(mask_bytes, format='PNG')
                                
                                result = generative_fill(
                                    st.session_state.api_key,
                                    uploaded_file.getvalue(),
                                    mask_bytes.getvalue(),
                                    prompt,
                                    negative_prompt=negative_prompt if negative_prompt else None,
                                    num_results=num_variations,
                                    sync=True
                                )
                                
                                if result and "result_urls" in result:
                                    st.session_state.generated_images = result["result_urls"]
                                    st.session_state.edited_image = result["result_urls"][0]
                                    st.session_state.history.append("Performed generative fill")
                                    st.success(f"✨ Generated {len(result['result_urls'])} variations!")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            with cols[1]:
                st.subheader("Result")
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, use_column_width=True)
                    
                    # Download button
                    img_data = download_image(st.session_state.edited_image)
                    if img_data:
                        st.download_button(
                            "⬇️ Download Result",
                            img_data,
                            "generated_fill.png",
                            "image/png",
                            key="dl_fill"
                        )
                    
                    # Variations if available
                    if st.session_state.get('generated_images') and len(st.session_state.generated_images) > 1:
                        st.subheader("Variations")
                        var_cols = st.columns(2)
                        for idx, img_url in enumerate(st.session_state.generated_images[1:3]):
                            with var_cols[idx % 2]:
                                st.image(img_url, use_column_width=True)
                                img_data = download_image(img_url)
                                if img_data:
                                    st.download_button(
                                        f"⬇️ Download Var {idx+1}",
                                        img_data,
                                        f"fill_variation_{idx+1}.png",
                                        "image/png",
                                        key=f"dl_fill_var_{idx}"
                                    )
                else:
                    st.info("👆 Generate content to see results here")
    
    # Erase Elements Tab - Enhanced
    with tabs[3]:
        st.header("AI Object Removal")
        st.markdown("Remove unwanted objects from your images seamlessly.")
        
        # Feature cards
        create_feature_card(
            "Smart Erase", 
            "AI automatically fills in the background after removal",
            "🧹"
        )
        create_feature_card(
            "Batch Processing", 
            "Remove multiple objects at once with complex masks",
            "🔄"
        )
        
        # Main content
        uploaded_file = st.file_uploader(
            "Upload Image to Edit", 
            type=["png", "jpg", "jpeg"], 
            key="erase_upload_v2"
        )
        
        if uploaded_file:
            cols = st.columns([1, 1])
            
            with cols[0]:
                st.subheader("Original Image")
                img = Image.open(uploaded_file)
                
                # Calculate canvas dimensions
                width, height = img.size
                aspect_ratio = height / width
                canvas_width = min(width, 700)
                canvas_height = int(canvas_width * aspect_ratio)
                
                # Create drawing canvas
                st.markdown("**Draw on the image to select areas to remove**")
                stroke_width = st.slider("Brush Size", 1, 50, 25, key="brush_size_erase")
                
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",
                    stroke_width=stroke_width,
                    stroke_color="#FF0000",
                    background_image=img.resize((canvas_width, canvas_height)),
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="freedraw",
                    key="canvas_erase"
                )
                
                # Advanced options
                with st.expander("⚙️ Advanced Options", expanded=False):
                    content_moderation = st.checkbox("Content Moderation", True)
                    enhance_result = st.checkbox("Enhance Result Quality", True)
                
                if st.button("🧹 Remove Selected", type="primary", key="erase_btn_v2"):
                    if canvas_result.image_data is None or not np.any(canvas_result.image_data[..., -1] > 0):
                        st.warning("Please select areas to remove first")
                    else:
                        with st.spinner("Removing selected objects..."):
                            try:
                                # Prepare mask
                                mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), mode='RGBA')
                                mask_img = mask_img.convert('L')
                                mask_bytes = io.BytesIO()
                                mask_img.save(mask_bytes, format='PNG')
                                
                                result = erase_foreground(
                                    st.session_state.api_key,
                                    uploaded_file.getvalue(),
                                    content_moderation=content_moderation
                                )
                                
                                if result and "result_url" in result:
                                    st.session_state.edited_image = result["result_url"]
                                    st.session_state.history.append("Removed objects from image")
                                    st.success("✨ Objects removed successfully!")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            with cols[1]:
                st.subheader("Result")
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, use_column_width=True)
                    
                    # Download button
                    img_data = download_image(st.session_state.edited_image)
                    if img_data:
                        st.download_button(
                            "⬇️ Download Result",
                            img_data,
                            "cleaned_image.png",
                            "image/png",
                            key="dl_erase"
                        )
                else:
                    st.info("👆 Select areas to remove and click the button")
    
    # Settings Tab
    with tabs[4]:
        st.header("Settings & Preferences")
        
        # App settings
        with st.expander("🛠️ Application Settings", expanded=True):
            app_cols = st.columns(2)
            with app_cols[0]:
                dark_mode = st.toggle("Dark Mode", False)
                animation_effects = st.toggle("Animation Effects", True)
            with app_cols[1]:
                image_quality = st.select_slider(
                    "Default Image Quality",
                    options=["Low", "Medium", "High", "Ultra"],
                    value="High"
                )
        
        # Account settings
        with st.expander("👤 Account Information", expanded=True):
            st.text_input("Name", "John Doe")
            st.text_input("Email", "john@example.com")
            if st.button("Save Account Info"):
                st.success("Account information saved!")
        
        # API information
        with st.expander("🔌 API Usage", expanded=True):
            if st.session_state.api_key:
                st.success("API Key: Configured")
                st.code(f"Last used: {time.strftime('%Y-%m-%d %H:%M')}")
                
                usage_cols = st.columns(3)
                with usage_cols[0]:
                    st.metric("This Month", "1,243", "12% ↑")
                with usage_cols[1]:
                    st.metric("Credits Left", "8,757", "87%")
                with usage_cols[2]:
                    st.metric("Avg. Cost", "$0.12", "5% ↓")
                
                st.progress(0.13)
            else:
                st.warning("No API key configured")
        
        # Support section
        with st.expander("❓ Help & Support", expanded=False):
            st.markdown("""
            ### Need help?
            - [Documentation](https://docs.pixeloom.ai)
            - [Community Forum](https://community.pixeloom.ai)
            - [Contact Support](mailto:support@pixeloom.ai)
            
            ### App Version
           DreamPixel  AI Studio v2.1.0
            """)

if __name__ == "__main__":
    main()