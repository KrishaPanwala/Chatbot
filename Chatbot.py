import google.generativeai as genai
import base64
import os
import streamlit as st
from PIL import Image
import io
import PyPDF2  # For PDF files
from docx import Document  # For DOCX files
import speech_recognition as sr
import pyttsx3
import re

GOOGLE_API_KEY = "Api"  # Replace with your actual key
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Text-to-speech setup
engine = pyttsx3.init()

# Speech-to-text setup
recognizer = sr.Recognizer()

text = "some text"
pattern = r"find_me"  # This pattern won't match

match = re.search(pattern, text)

if match:
    result = match.group(0)  # Access the match
    print(result)
else:
    print("No match found")

def get_gemini_response(prompt, history=[]):
    system_prompt = "You are a helpful and informative chatbot. Answer questions clearly and concisely."
    try:
        if history:
            full_prompt = "\n".join(history) + "\n" + prompt
        else:
            full_prompt = prompt
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def summarize_text(text):
    prompt = f"Summarize the following text:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def analyze_image(image_file, prompt):
    try:
        img = Image.open(image_file)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_data = {"mime_type": "image/jpeg", "data": encoded_image}

        contents = [
            prompt,
            image_data
        ]

        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"An image analysis error occurred: {e}"

def read_document(file):
    file_type = file.type
    if "text/plain" in file_type:
        return file.getvalue().decode("utf-8")
    elif "application/pdf" in file_type:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in file_type:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    else:
        return "Unsupported file type."

def document_summarization_interface():
    st.title("Document Summarization")
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        with st.spinner("Summarizing..."):
            document_text = read_document(uploaded_file)
            if "Unsupported file type" not in document_text:
                summary = summarize_text(document_text)
                st.write("Summary:")
                st.write(summary)
            else:
                st.write(document_text)

def chat_interface():
    st.title("Chatbot Interface")
    st.write("Welcome to the Q&A Chatbot! Type 'summarize:' followed by text to summarize.")
    history = []
    user_input = st.text_input("You:")
    if st.button("Send"):
        if user_input.lower() in ["quit", "exit", "bye"]:
            st.write("Chatbot: Goodbye!")
        elif user_input.lower().startswith("summarize:"):
            text_to_summarize = user_input[len("summarize:"):].strip()
            summary = summarize_text(text_to_summarize)
            st.write("Chatbot Summary:", summary)
            history.append("You: " + user_input)
            history.append("Chatbot: " + summary)
        else:
            response = get_gemini_response(user_input, history)
            st.write("Chatbot:", response)
            history.append("You: " + user_input)
            history.append("Chatbot: " + response)

def image_analysis_interface():
    st.title("Image Analysis Interface")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image.", use_column_width=True)
        prompt = st.text_input("Enter your prompt:", "Describe this image.")
        if st.button("Analyze Image"):
            with st.spinner("Analyzing..."):
                result = analyze_image(uploaded_file, prompt)
                st.write("Analysis Result:")
                st.write(result)

def speak(text):
    try:
        # Say the text
        engine.say(text)

        # Run the speech event loop, if it's not already running
        engine.runAndWait()
    
    except RuntimeError:
        # Handle the case where the loop is already running
        print("Warning: The speech engine is already running. Skipping 'runAndWait' this time.")
    
def listen():
    with sr.Microphone() as source:
        st.write("Listening... (you have 5 seconds)")
        audio = recognizer.listen(source, timeout=5)  # Add timeout to prevent waiting indefinitely
        try:
            text = recognizer.recognize_google(audio)
            st.write(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.write("Could not understand audio")
            return None
        except sr.RequestError as e:
            st.write(f"Could not request results; {e}")
            return None


def voice_assistant_interface():
    st.title("Voice Assistant Chatbot")
    history = []

    if st.button("Start Listening"):
        user_input = listen()
        if user_input:
            response = get_gemini_response(user_input, history)
            st.write(f"Chatbot: {response}")
            speak(response)
            history.append(f"You: {user_input}")
            history.append(f"Chatbot: {response}")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a page", ["Chatbot", "Image Analysis", "Document Summarization", "Voice Assistant"])

if page == "Chatbot":
    chat_interface()
elif page == "Image Analysis":
    image_analysis_interface()
elif page == "Document Summarization":
    document_summarization_interface()
elif page == "Voice Assistant":
    voice_assistant_interface()
