import streamlit as st

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import base64
import pandas as pd
import matplotlib.pyplot as plt
from skllm.config import SKLLMConfig
from skllm.models.gpt.text2text.summarization import GPTSummarizer
import openai
from openai import OpenAI
from wordcloud import WordCloud
import subprocess
import time
import numpy as np
import ast #built in
from annotated_text import annotated_text
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

x = "No"

api_key = st.secrets["api"]['api_key']
openai.api_key = api_key
credentials = st.secrets["gcp_service_account"]
client = OpenAI(api_key=api_key)

@st.cache_data
def user_avatar_pi():
  # Load the image and convert it to base64
  with open('data/avatar_user.png', 'rb') as image_file_user_pi:
    encoded_string_user_pi = base64.b64encode(image_file_user_pi.read()).decode()
  # Base64 encoded image string from the previous step
  avatar_base64_user_pi = encoded_string_user_pi  # This is the base64 string you got earlier
  
  # Construct the base64 image string for use in HTML
  avatar_url_user_pi = f'data:image/png;base64,{avatar_base64_user_pi}'
  return avatar_url_user_pi

avatar_url_user_pi = user_avatar_pi()

def show_user_answer_pi(message_text,avatar_url_user_pi):
  st.markdown(f"""
  <div style='display: flex; align-items: flex-start; padding: 10px; justify-content: flex-end;'>
      <div style='background-color: #F7F9FA; padding: 10px 15px; border-radius: 10px; margin-right: 10px; display: inline-block; text-align: right; max-width: 60%; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);'>
          <span style='font-size: 16px;'>{message_text}</span>
      </div>
      <div style='flex-shrink: 0;'>
          <img src='{avatar_url_user_pi}' alt='avatar' style='width: 40px; height: 40px; border-radius: 50%; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);'>
      </div>
  </div>
  """, unsafe_allow_html=True)

#### AI AVATAR AND RESPONSE
@st.cache_data
def ai_avatar_pi():
  # Load the image and convert it to base64
  with open('data/avatar_ai_pi.png', 'rb') as image_file_pi:
    encoded_string_pi = base64.b64encode(image_file_pi.read()).decode()
  # Base64 encoded image string from the previous step
  avatar_base64_pi = encoded_string_pi  # This is the base64 string you got earlier
  
  # Construct the base64 image string for use in HTML
  avatar_pi = f'data:image/png;base64,{avatar_base64_pi}'
  return avatar_pi

avatar_pi = ai_avatar_pi()

def show_ai_response_pi(message_text,avatar_pi):
  st.markdown(f"""
  <div style='display: flex; align-items: flex-start; padding: 10px; justify-content: flex;'>
      <div style='flex-shrink: 0;'>
          <img src='{avatar_pi}' alt='avatar' style='width: 40px; height: 40px; border-radius: 50%; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);'>
      </div>
      <div style='background-color: #FCFCFC; padding: 10px 15px; border-radius: 10px; margin-left: 10px; display: inline-block; text-align: left; max-width: 85%; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);'>
          <span style='font-size: 16px;'>{message_text}</span>
      </div>

  </div>
  """, unsafe_allow_html=True)
    
class ChatHistory:
    def __init__(self):
        self.history = []

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []

    def show_history(self):
        for msg in self.history:
            role = msg['role']
            content = msg['content']
            st.write(f"{role.capitalize()}: {content}")

    def show_history_streamlit(self):
        for msg in self.history:
            role = msg['role']
            content = msg['content']
            # st.chat_message(role).write(content)
            if role == "user":
                show_user_answer_pi(content,avatar_url_user_pi)
            elif role == "assistant":
                show_ai_response_pi(content,avatar_pi)
               
    def get_latest_messages(self, count=4):
        return self.history[-count:]

@st.cache_resource
def load_collection():
    CHROMA_DATA_PATH = 'program_info_7'
    COLLECTION_NAME = f"{CHROMA_DATA_PATH}_embeddings"
    client_chromadb = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=openai.api_key, model_name="text-embedding-ada-002")
    vector_store = client_chromadb.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"}
    )
    return vector_store
  
if 'vector_store' not in st.session_state:
  st.session_state.vector_store = load_collection()

def retrieve_documents(query, collection):
    results = collection.query(query_texts=[query], n_results=3)
    docs = results['documents'][0]
    metadatas = results['metadatas'][0]
    return [{"text": doc, "metadata": meta} for doc, meta in zip(docs, metadatas)]

def generate_chatbot_response(context, query, metadata, chat_memory):
    # prompt components
    history_text = ""
    metadata_info = ""

    # Check if chat memory is not empty and add to history_text if not empty
    if chat_memory:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_memory])

    #Check if metadata is not empty and add to metadata_info if not empty
    if metadata:
        metadata_info = "\n".join([f"File: {meta['description']}" for meta in metadata])

    # UPDATED PROMPTS
    if history_text:
        prompt = f"Consider following conversation history if necessary:\n\n{history_text}\n\nCurrent Information:\n\n{context}\n\nAdditional Information:\n{metadata_info}\n\nAnswer the following question:\n{query}"
    else:
        prompt = f"Based on the following information:\n\n{context}\n\nAdditional Information:\n{metadata_info}\n\nAnswer the following question:\n{query}"


    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that helps students answer questions about Eskwelabs' Data Science Fellowship program."},
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.choices[0].message.content.strip()

    #Fallback message
    if not response_text or "unknown" in response_text.lower():
        response_text = "I couldn't find any relevant information based on your query. Please try rephrasing your question or providing more details."

    return response_text
    
def chatbot_response(user_query, collection, chat_history, chat_memory):
    chat_history.add_message("user", user_query)
    
    retrieved_docs = retrieve_documents(user_query, collection)
    context = ' '.join([doc['text'] for doc in retrieved_docs])
    response = generate_chatbot_response(context, user_query, [doc['metadata'] for doc in retrieved_docs], chat_memory)
    
    chat_history.add_message("assistant", response)
    st.session_state.question_pi_bool = False
    return response

@st.fragment
def update_chat_memory():
    st.session_state.pi_chat_memory = st.session_state.pi_chat_history.get_latest_messages()
    st.rerun()

def show_pi_chat_memory():
    for msg in st.session_state.pi_chat_memory:
        role = msg['role']
        content = msg['content']
        # st.chat_message(role).write(content)
        if role == "user":
            show_user_answer_pi(content,avatar_url_user_pi)
        elif role == "assistant":
            show_ai_response_pi(content,avatar_pi)
          
# Initialize chat history in session state
if 'pi_chat_history' not in st.session_state:
    st.session_state.pi_chat_history = ChatHistory()

# Initialize chat history in session state
if 'pi_chat_memory' not in st.session_state:
    st.session_state.pi_chat_memory = []
  
# Initialize session state for button clicks
if 'button_clicked_pi' not in st.session_state:
    st.session_state.button_clicked_pi = False

# Initialize session state for question
if 'question_pi' not in st.session_state:
    st.session_state.question_pi = ""

if 'question_pi_bool' not in st.session_state:
    st.session_state.question_pi_bool = False


########################################## MAIN PROGRAM ##########################################
with st.sidebar:
    if st.button("Start Over", type = "primary", use_container_width = True, help = "Restart Chat Session"):
        st.session_state.pi_chat_history.clear_history()
        st.session_state.pi_chat_memory = []  # Clear chat memory as well   
        st.session_state.button_clicked_pi = False
        st.session_state.question_pi = ""
        st.rerun()
      
# with st.sidebar:
#   # Call this function to load test answers at the beginning of your app (or when you need to test)
#   st.image('data/John.png', use_column_width=True)
#   st.markdown(
#       """
#       <div style="font-family: 'Arial', sans-serif; padding: 10px; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
#           <p style="font-size: 11px; color: #333;">
#               "To learn more, John turns to the Program Information Bot. He asks, <strong>'How do I apply?'</strong> The bot provides him with the steps he needs to follow, 
#               including taking the Pathfinder Assessment, scheduling a Fit Interview, and selecting a payment option. John then follows up with, 
#               <strong>'For step 2, what should I expect, and how can I best prepare for it?'</strong> The bot explains that the Fit Interview will focus on his background, 
#               goals, and alignment with the program. It gives John guidance on how to effectively prepare, helping him feel confident and ready to make a strong impression."
#           </p>
#       </div>
#       """,
#       unsafe_allow_html=True
#   )
        
user_query = st.chat_input("Ask Eskwelabs")
if user_query:
    st.session_state.button_clicked_pi = True
    response = chatbot_response(user_query, st.session_state.vector_store, st.session_state.pi_chat_history, st.session_state.pi_chat_memory)
    update_chat_memory()
#################################################################################################

col111, col222, col333 = st.columns([1,4,1])
with col222:
  st.markdown("""<h1 style='text-align: center;'>Eskwelabs Data Science Fellowship Information Bot</h1>""", unsafe_allow_html=True)
  cc11, cc22, cc33 = st.columns([1,10,1])
  with cc22:
    st.markdown(f"""<h6 style='text-align: center;'><i>This AI-powered assistant chatbot is designed to help you with ideas, advice, and questions that you may have to understand all aspects of the Eskwelabs DSF program.</h6>""", unsafe_allow_html=True)
    st.session_state.pi_chat_history.show_history_streamlit()   


  if st.session_state.button_clicked_pi == False:

      st.markdown("<br>", unsafe_allow_html = True)       
      
      bb00, bb01, bb02, bb03, bb04 = st.columns([1,1,1,1,1])
      bot_stats = "I have a validity/reliability rate of 94%!" 
      with bb02:
        st.markdown(
        f"""
        <style>
        .tooltip {{
          position: relative;
          display: inline-block;
          cursor: pointer;
        }}
    
        .tooltip .tooltiptext {{
          visibility: hidden;
          width: 250px;
          background-color: #fff;
          color: #333;
          text-align: left; /* Align text to the left */
          border-radius: 5px;
          padding: 10px;
          position: absolute;
          z-index: 1;
          left: 100%; /* Position next to the image */
          top: 50%;
          transform: translateX(20%) translateY(-50%); /* Center tooltip box */
          opacity: 0;
          transition: opacity 0.3s;
          white-space: normal; /* Allow text to wrap */
          display: flex;
          align-items: flex-end; /* Align content to the bottom */
          justify-content: flex-start; /* Align content to the left */
          box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
          font-size: 12px;
        }}
    
        .tooltip:hover .tooltiptext {{
          visibility: visible;
          opacity: 1;
        }}
        </style>
        <div style='display: flex; align-items: center; justify-content: center; width: 100%;'>
            <div class='tooltip' style='flex-shrink: 0; width: 100%;'>
                <img src='{avatar_pi}' style='width: 100%; height: auto; object-fit: contain;'>
                <span class="tooltiptext">{bot_stats}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
        )
        
      st.markdown(f"<h6 style='text-align: center;'><br><br>Choose a question to get started or ask Eskwelabs below:</h6>", unsafe_allow_html=True)

    
      bb0, bb1, bb2, bb3, bb4 = st.columns([0.5,1,1,1,0.5])
      bbb0, bbb1, bbb2, bbb3 = st.columns([0.5, 1, 1, 0.5])
        
      with bb1:
        if st.button("What is the schedule of the bootcamp?", use_container_width = True): # What is the DSF program guide about?
          st.session_state.question_pi = "What is the schedule of the bootcamp?" # What is the DSF program guide about?
          st.session_state.button_clicked_pi = True
          st.session_state.question_pi_bool = True
          st.rerun()
          
      with bb3:
        if st.button("When is the next bootcamp?", use_container_width = True):
          st.session_state.question_pi = "When is the next bootcamp?"
          st.session_state.button_clicked_pi = True
          st.session_state.question_pi_bool = True
          st.rerun()
          

      with bbb1:
        if st.button("How do I apply?", use_container_width = True):
          st.session_state.question_pi = "How do I apply?"
          st.session_state.button_clicked_pi = True
          st.session_state.question_pi_bool = True
          st.rerun()
          
      with bb2:
        if st.button("How much is the payment?", use_container_width = True): # What is the DSF program guide about?
          st.session_state.question_pi = "How much is the payment?" # What is the DSF program guide about?
          st.session_state.button_clicked_pi = True
          st.session_state.question_pi_bool = True
          st.rerun()
          
      with bbb2:
        if st.button("Recommend Educational Materials for Beginners", use_container_width = True):
          st.session_state.question_pi = "Recommend Educational Materials for Beginners"
          st.session_state.button_clicked_pi = True
          st.session_state.question_pi_bool = True
          st.rerun()
  
  if st.session_state.question_pi_bool == True:       
    st.session_state.response_pi = chatbot_response(st.session_state.question_pi, st.session_state.vector_store, st.session_state.pi_chat_history, st.session_state.pi_chat_memory)
    update_chat_memory()
