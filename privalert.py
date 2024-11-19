import streamlit as st
from PIL import Image
import base64
import os
from groq import Groq
import logging
import time


# Initialize Groq client with secrets
client = Groq(api_key=st.secrets["general"]["api_key"])  # Use the API key from secrets

# Other constants
llama_3_2_Vision_11B = 'llama-3.2-90b-vision-preview'
llama32_model = 'llama-3.2-3b-preview'

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to convert image to text
def image_to_text(client, model, base64_image, prompt):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        model=model
    )
    return chat_completion.choices[0].message.content

# Function to generate a document analysis
def document_analysis_generation(client, image_description):
    chat_completion = client.chat.completions.create(   
        messages=[
            {
                "role": "system",
                #"content": "Give me a bold output if it contains Personal Identifiable information. If it does, then mask the information that would make the person's identity vulnerable",
                "content": "Give me a Output which explains about the text if it has Personally Identifiable Information (PII) give it in the output and write No PII Detected as output",
            },
            {
                "role": "user",
                "content": image_description,
            }
        ],
        model=llama32_model
    )
    return chat_completion.choices[0].message.content

# Function to add custom background
def add_bg_from_url(image_url):
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{image_url}");
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# Custom CSS with updated color scheme and background options
def set_custom_style(bg_color=None, bg_image=None):
    style = """
    <style>
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #34495e;
        --accent-color: #3498db;
        --text-color: #2c3e50;
        --sidebar-color: rgba(189, 195, 199, 0.7);
    }
    .reportview-container {
        color: var(--text-color);
    }
    .sidebar .sidebar-content {
        background-color: var(--sidebar-color);
    }
    .stButton>button {
        background-color: var(--accent-color);
        color: white;
    }
    .stTextInput>div>input, .stTextArea>div>textarea {
        background-color: rgba(255, 255, 255, 0.8);
        color: var(--text-color);
        border: 1px solid var(--primary-color);
    }
    .stAlert {
        background-color: rgba(231, 76, 60, 0.8);
        color: white;
    }
    .output-container {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        border-left: 5px solid var(--accent-color);
    }
    h1, h2, h3 {
        color: var(--primary-color);
    }
    .stExpander {
        border: 1px solid var(--secondary-color);
        border-radius: 5px;
    }
    .stExpander > div > div > div > div {
        background-color: rgba(255, 255, 255, 0.8);
    }
    """
    if bg_color:
        style += f"""
        .stApp {{
            background-color: {bg_color};
        }}
        """
    elif bg_image:
        style += f"""
        .stApp {{
            background-image: url("{bg_image}");
            background-attachment: fixed;
            background-size: cover;
        }}
        """
    style += "</style>"
    st.markdown(style, unsafe_allow_html=True)

# Streamlit app layout
st.set_page_config(page_title="PrivAlert", page_icon="🔒", layout="wide")

# Sidebar
with st.sidebar:
    st.title("PrivAlert Settings")
    st.markdown('<hr style="margin: 15px 0;">', unsafe_allow_html=True)
    
    # Background options
    bg_option = st.radio("Choose background:", ("Default", "Color", "Image"))
    if bg_option == "Color":
        bg_color = st.color_picker("Pick a background color", "#f0f0f0")
        set_custom_style(bg_color=bg_color)
    elif bg_option == "Image":
        bg_image = st.text_input("Enter image URL:")
        if bg_image:
            set_custom_style(bg_image=bg_image)
    else:
        set_custom_style()

    enable_logging = st.checkbox("Enable Data Logging")
    if enable_logging:  # Popup notification for logging
        st.success("Data logging is enabled. Logs will be saved to 'app.log'.")
        # Set up logging configuration here
        logging.basicConfig(filename='app.log', level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
    
    if st.button("Clear Inputs"):
        st.session_state.clear()
        st.success("Inputs cleared.")  # Display a message instead of rerunning

# Main content
st.title("PrivAlert: Privacy-Focused Document Analysis")
st.markdown('<hr style="margin: 15px 0;">', unsafe_allow_html=True)  # Added horizontal rule

# Temporary placeholder for PII warning
pii_warning_placeholder = st.empty()

# Two-column layout
col1, col2 = st.columns(2)

# Column 1: Image Input
with col1:
    st.header("Image Input")
    uploaded_file = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        image_path = f"temp_image.{uploaded_file.name.split('.')[-1]}"
        image.save(image_path)
        base64_image = encode_image(image_path)

# Column 2: Text Prompt
with col2:
    st.header("Text Prompt")
    prompt = st.text_area("Enter your prompt (e.g., Describe this image):")

# Process Button
if st.button("Process Image"):
    if uploaded_file is not None and prompt:
        if enable_logging:  # Log when processing starts
            logging.info("Processing image with prompt: %s", prompt)
        # Log image upload
        if uploaded_file is not None:
            logging.info("User uploaded an image: %s", uploaded_file.name)
        # Log prompt entry
        logging.info("User entered prompt: %s", prompt)
        with st.spinner("Processing image..."):
            # Image Description
            image_description = image_to_text(client, llama_3_2_Vision_11B, base64_image, prompt)
            if enable_logging:  # Log the image description
                logging.info("Image description generated: %s", image_description)
            st.subheader("Image Description")
            with st.expander("View Image Description", expanded=True):
                st.markdown(f'<div class="output-container">{image_description}</div>', unsafe_allow_html=True)

            # Document Analysis
            analysis = document_analysis_generation(client, image_description)
            if enable_logging:  # Log the analysis result
                logging.info("Document analysis result: %s", analysis)
            st.subheader("Privacy Analysis")
            with st.expander("View Privacy Analysis", expanded=True):
                st.markdown(f'<div class="output-container">{analysis}</div>', unsafe_allow_html=True)

            # Check for No PII Detected first
            if "No PII Detected" in analysis or "No Personal Identifiable Information Found" in analysis or "No Sensitive Information Detected" in analysis:
                # Green alert for No PII Detected
                st.markdown(
                    """
                    <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb;">
                        <h3 style="color: #155724;">✅ No PII Detected</h3>
                        <p style="color: #155724;">The analysis did not find any Personal Identifiable Information (PII). Your data is safe.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # Check for PII in the analysis
            elif "PII" in analysis or "Personal Identifiable Information" in analysis:
                # Red alert for PII detected
                st.warning("⚠️ Personal Identifiable Information (PII) detected! Please review the analysis carefully.")
                if enable_logging:  # Log PII detection
                    logging.warning("PII detected in analysis.")
    else:
        st.error("Please upload an image and enter a prompt.")
        if enable_logging:  # Log error for missing inputs
            logging.error("User did not upload an image or enter a prompt.")

# Footer
st.markdown("---")
st.markdown("PrivAlert © 2024 | Protecting Your Privacy")
