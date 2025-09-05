import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def get_model():

    st.sidebar.subheader("Model Selection")

    # Options for model type
    opt_paid_free = st.sidebar.radio(
    "Choose Model",
    ["Free (Limited)", "Free (using API)", "Paid (using API)"],
    index=1,
    horizontal=True,
    help="To use via API, first create an API key from their official website. \n[learn more](https://github.com/Sachin8871/SQL-Agent/blob/main/README.md)"
)


    #=============================================== Free Models ======================================================

    if opt_paid_free == "Free (Limited)":
        # Options for free models
        model_name = st.sidebar.selectbox(label="Select Model", options=["GroqAI-llama-3.3-70b-versatile", "gemini-2.5-flash-lite"])
        
        if model_name == "GroqAI-llama-3.3-70b-versatile":  # Groq
            return ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=st.secrets['API']['GROQ_API_KEY'])

        elif model_name == "gemini-2.5-flash-lite":  # Gemini
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=st.secrets['API']['GEMINI_API_KEY'])


    #============================================ Free Models using API ==================================================

    elif opt_paid_free == "Free (using API)":
        # Options for free models using API
        model_name = st.sidebar.selectbox(label="Select Model", options=["GroqAI-llama-3.3-70b-versatile","GroqAI-deepseek-r1-distill-llama-70b", "gemini-2.5-flash-lite"])

        if model_name == "GroqAI-llama-3.3-70b-versatile":  # Groq -> llama
            groq_key = st.sidebar.text_input("🔑 Groq API Key", type="password")
            if groq_key:
                return ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key)
            else:
                st.error("Please enter your Groq API Key.")

        elif model_name == "GroqAI-deepseek-r1-distill-llama-70b":  # Groq -> Deepseek
            groq_key = st.sidebar.text_input("🔑 Groq API Key", type="password")
            if groq_key:
                return ChatGroq(model="deepseek-r1-distill-llama-70b", groq_api_key=groq_key)
            else:
                st.error("Please enter your Groq API Key.")

        elif model_name == "gemini-2.5-flash-lite":  # Gemini
            google_key = st.sidebar.text_input("🔑 Google Gemini API Key", type="password")
            if google_key:
                return ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=google_key)
            else:
                st.error("Please enter your Gemini API Key.")

             
    #============================================ Paid Models using API ==================================================

    elif opt_paid_free == "Paid (using API)":
        # Options for paid models
        model_name = st.sidebar.selectbox(label="Select Model", options=["GPT-4 Turbo", "GPT-4 Turbo", "Gemini 1.5 Pro"])

        if model_name == "GPT-3.5 Turbo":  # Openai's GPT-3.5
            openai_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
            if openai_key:
                return ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=openai_key)
            else:
                st.error("Please enter your OpenAI API Key.")

        elif model_name == "GPT-4 Turbo":  # Openai's GPT-4.0
            openai_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
            if openai_key:
                return ChatOpenAI(model="gpt-4-turbo", openai_api_key=openai_key)
            else:
                st.error("Please enter your OpenAI API Key.")

        elif model_name == "Gemini 1.5 Pro":  # Google's gemini 1.5 pro
            google_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")
            if google_key:
                return ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=google_key)
            else:
                st.error("Please enter your Gemini API Key.")
    
    else:
        st.warning("Choose Free or Paid Model")


#=============================================== END ==================================================
