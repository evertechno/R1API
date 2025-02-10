import streamlit as st
import google.generativeai as genai
import requests
import time
import os
import random

# ---- Helper Functions ----

def initialize_session():
    """Initializes session state variables."""
    if 'session_count' not in st.session_state:
        st.session_state.session_count = 0
    if 'block_time' not in st.session_state:
        st.session_state.block_time = None

def check_session_limit():
    """Checks if the user has reached the session limit and manages block time."""
    if st.session_state.block_time:
        time_left = st.session_state.block_time - time.time()
        if time_left > 0:
            st.error(f"You have reached your session limit. Please try again in {int(time_left)} seconds.")
            st.write("Upgrade to Pro for unlimited content generation.")
            st.stop()
        else:
            st.session_state.block_time = None

    if st.session_state.session_count >= 5:
        st.session_state.block_time = time.time() + 15 * 60  # Block for 15 minutes
        st.error("You have reached the session limit. Please wait for 15 minutes or upgrade to Pro.")
        st.write("Upgrade to Pro for unlimited content generation.")
        st.stop()

def generate_content(prompt, model_name, api_key):
    """Generates content using Generative AI with the specified API key."""
    try:
        # Configure the Generative AI model with the appropriate API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating content: {e}")
        raise

def search_web(query):
    """Searches the web using Google Custom Search API and returns results."""
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_SEARCH_ENGINE_ID"],
        "q": query,
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        st.error(f"Search API Error: {response.status_code} - {response.text}")
        return []

def get_next_model_and_key():
    """Cycle through available models and corresponding API keys in a round-robin fashion."""
    models_and_keys = [
        ('gemini-1.5-flash', st.secrets["API_KEY_GEMINI_1_5_FLASH"]),
        ('gemini-2.0-flash', st.secrets["API_KEY_GEMINI_2_0_FLASH"]),
        ('gemini-1.5-flash-8b', st.secrets["API_KEY_GEMINI_1_5_FLASH_8B"]),
        ('gemini-2.0-flash-exp', st.secrets["API_KEY_GEMINI_2_0_FLASH_EXP"])
    ]
    
    # Select a model and corresponding key randomly for round-robin distribution
    model, api_key = random.choice(models_and_keys)
    return model, api_key

# ---- Streamlit App ----

# Configure the API keys securely using Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# App Title and Description
st.title("AI-Powered Ghostwriter")
st.write("Generate high-quality content and check for originality using the power of Generative AI and Google Search.")

# Initialize session tracking
initialize_session()

# Prompt Input Field
prompt = st.text_area("Enter your prompt:", placeholder="Write a blog about AI trends in 2025.")

# Session management to check for block time and session limits
check_session_limit()

# Generate Content Button
if st.button("Generate Response"):
    if not prompt.strip():
        st.error("Please enter a valid prompt.")
    else:
        try:
            # Get the next model and its corresponding API key
            model, api_key = get_next_model_and_key()

            # Generate content using Generative AI
            generated_text = generate_content(prompt, model, api_key)

            # Increment session count
            st.session_state.session_count += 1

            # Display the generated content
            st.subheader("Generated Content:")
            st.write(generated_text)

            # Check for similar content online
            st.subheader("Searching for Similar Content Online:")
            search_results = search_web(generated_text)

            if search_results:
                st.warning("Similar content found on the web:")

                for result in search_results[:5]:  # Show top 5 results
                    with st.expander(result['title']):
                        st.write(f"**Source:** [{result['link']}]({result['link']})")
                        st.write(f"**Snippet:** {result['snippet']}")
                        st.write("---")

                st.warning("To ensure 100% originality, you can regenerate the content.")
                if st.button("Regenerate Content"):
                    regenerate_and_display_content(generated_text)
            else:
                st.success("No similar content found online. Your content seems original!")

        except Exception as e:
            st.error(f"Error generating content: {e}")

# Regenerate Content and Ensure Originality
def regenerate_and_display_content(original_text):
    """Regenerates content and displays it after ensuring originality."""
    model, api_key = get_next_model_and_key()
    prompt = f"Rewrite the following content to make it original and distinct. Ensure it is paraphrased and does not match existing content:\n\n{original_text}"
    
    regenerated_text = generate_content(prompt, model, api_key)
    st.success("Content has been regenerated for originality.")
    st.subheader("Regenerated Content:")
    st.write(regenerated_text)

# Display regenerated content if available
if 'generated_text' in st.session_state:
    st.subheader("Regenerated Content (After Adjustments for Originality):")
    st.write(st.session_state.generated_text)
