import streamlit as st
import sqlite3
__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import openai
import streamlit as st
# import os
from openai import OpenAI
# from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import base64
api_key = st.secrets["api"]['api_key']
openai.api_key = api_key
credentials = st.secrets["gcp_service_account"]
client = OpenAI(api_key=api_key)

# Load environment variables from .env file
# load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=api_key)


@st.cache_resource
def load_collection_DSFBAssistant():
  CHROMA_DATA_PATH_2 = "eskwe"
  COLLECTION_NAME_2 = "eskwe_embeddings"
  client_chromadb_2 = chromadb.PersistentClient(path=CHROMA_DATA_PATH_2)
  openai_ef_2 = embedding_functions.OpenAIEmbeddingFunction(api_key=openai.api_key, model_name="text-embedding-ada-002")
  collection = client_chromadb_2.get_or_create_collection(
    name=COLLECTION_NAME_2,
    embedding_function=openai_ef_2,
    metadata={"hnsw:space": "cosine"}
  )
  return collection



collection = load_collection_DSFBAssistant()

#### USER AVATAR AND RESPONSE
@st.cache_data
def user_avatar():
  # Load the image and convert it to base64
  with open('data/avatar_user.png', 'rb') as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()
  # Base64 encoded image string from the previous step
  avatar_base64 = encoded_string  # This is the base64 string you got earlier
  
  # Construct the base64 image string for use in HTML
  avatar_url = f'data:image/png;base64,{avatar_base64}'
  return avatar_url

avatar_user = user_avatar()

def show_user_question(message_text,avatar_url):
  # Markdown to replicate the chat message
  # avatar_url = "https://avatars.githubusercontent.com/u/45109972?s=40&v=4"  # Replace this with any avatar URL or a local file path
  

  st.markdown(f"""
  <div style='display: flex; align-items: flex-start; padding: 10px; justify-content: flex-end;'>
      <div style='background-color: #F7F9FA; padding: 10px 15px; border-radius: 10px; margin-right: 10px; display: inline-block; text-align: right; max-width: 60%;'>
          <span style='font-size: 16px;'>{message_text}</span>
      </div>
      <div style='flex-shrink: 0;'>
          <img src='{avatar_url}' alt='avatar' style='width: 40px; height: 40px; border-radius: 50%;'>
      </div>
  </div>
  """, unsafe_allow_html=True)

#### AI AVATAR AND RESPONSE
@st.cache_data
def ai_avatar():
  # Load the image and convert it to base64
  with open('data/avatar_ai.png', 'rb') as image_file_ai:
    encoded_string_ai = base64.b64encode(image_file_ai.read()).decode()
  # Base64 encoded image string from the previous step
  avatar_base64_ai = encoded_string_ai  # This is the base64 string you got earlier
  
  # Construct the base64 image string for use in HTML
  avatar_ai = f'data:image/png;base64,{avatar_base64_ai}'
  return avatar_ai

avatar_ai = ai_avatar()

def show_ai_response(message_text,avatar_ai):
  # Markdown to replicate the chat message
  # avatar_url = "https://avatars.githubusercontent.com/u/45109972?s=40&v=4"  # Replace this with any avatar URL or a local file path
  

  st.markdown(f"""
  <div style='display: flex; align-items: flex-start; padding: 10px; justify-content: flex;'>
      <div style='flex-shrink: 0;'>
          <img src='{avatar_ai}' alt='avatar' style='width: 40px; height: 40px; border-radius: 50%;'>
      </div>
      <div style='background-color: #FCFCFC; padding: 10px 15px; border-radius: 10px; margin-left: 10px; display: inline-block; text-align: left; max-width: 85%;'>
          <span style='font-size: 16px;'>{message_text}</span>
      </div>

  </div>
  """, unsafe_allow_html=True)



# Function to find the best matching data in the collection based on user input
def return_best_eskdata(user_input, collection, n_results=3):
    query_result = collection.query(query_texts=[user_input], n_results=n_results)
    if not query_result['ids'] or not query_result['ids'][0]:
        return []
    
    # Collect the top N results
    results = []
    for i in range(n_results):
        if i < len(query_result['ids'][0]):
            top_result_metadata = query_result['metadatas'][0][i]
            top_result_document = query_result['documents'][0][i]
            # Extract the link from the metadata or document
            link = top_result_document.split('Link: ')[1].split('\n')[0] if 'Link: ' in top_result_document else 'No Link Found'
            results.append({
                "title": top_result_metadata.get('eskdata', 'Unknown Data'),
                "document": top_result_document,
                "link": link
            })
    return results

# Function to generate a conversational response using OpenAI API with document-based initial response
def generate_conversational_response(user_input, collection):
    # Step 1: Query for the most relevant document
    related_articles = return_best_eskdata(user_input, collection, n_results=3)
    
    if not related_articles:
        return "I couldn't find any relevant articles based on your input."

    # Use the retrieved document to form the initial response
    primary_article = related_articles[0]  # Use the most relevant article
    document_content = primary_article['document'][:1000]  # Limit the document content to a reasonable length

    # Step 2: Generate a conversational response using the document content
    conversation_prompt = (
        f"Based on the following information, please provide a friendly and conversational explanation:\n\n"
        f"{document_content}\n\n"
        f"Please also recommend the reader to explore more using this link: {primary_article['link']}"
    )

    try:
        conversational_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly assistant who provides clear and engaging explanations."},
                {"role": "user", "content": conversation_prompt}
            ],
            max_tokens=1000,
        )
        final_response_content = conversational_response.choices[0].message.content

        # Step 3: Prepare related articles section
        if len(related_articles) > 1:
            related_content = "Here are some additional related articles you might find useful:\n"
            for article in related_articles[1:]:
                related_content += f"- **{article['title']}**: [Read more]({article['link']})\n"
        else:
            related_content = "No additional related articles were found."

        # Combine the final response with related articles
        final_response = f"{final_response_content}\n\n{related_content}"
        
        return final_response
    
    except Exception as e:
        st.error(f"An error occurred with OpenAI API: {e}")
        return "An error occurred while generating the response."


# Streamlit UI
# st.title("Data Science Bootcamp Assistant")

# st.write("Ask any question related to the bootcamp, and get recommendations and answers.")
# with st.container():
#   user_input = st.chat_input("Enter your question:")
#   if user_input:
#       response = generate_conversational_response_DSFBAssistant(user_input, collection)
#       st.write(f"You asked: {user_input}")  
#       st.write(response)



ba1, ba2, ba3 = st.columns([1,4,1])


# Initialize session state for button clicks
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

    
# Initialize session state for question
if 'question' not in st.session_state:
  st.session_state.question = ""


########################################## MAIN PROGRAM ##########################################
# Allow the user to enter their own question after clicking a starter question
user_input = st.chat_input("Enter your question:")
if user_input:
    st.session_state.button_clicked = True
    st.session_state.question = user_input
    st.rerun()

with st.sidebar:
    if st.button("Start Over", type = "primary", use_container_width = True, help = "Restart Chat Session"):
        st.session_state.button_clicked = False
        st.session_state.question = "" 
        st.rerun()
#################################################################################################

  
with ba2:
  st.markdown(f"<h1 style='text-align: center;'>Data Science Bootcamp Assistant</h1>", unsafe_allow_html=True)
  st.markdown(f"<h6 style='text-align: center;'><i>Ask any question related to the bootcamp, and get recommendations and answers.</i></h6>", unsafe_allow_html=True)
  # Add conversation starters if no button has been clicked yet
  if st.session_state.button_clicked == False:

      
      st.markdown("<br><br><br><br><br>", unsafe_allow_html = True)       
      
      b00, b01, b02, b03, b04 = st.columns([1,1,1,1,1])
      with b02:
        st.image('data/avatar_ai.png', use_column_width =True)
      st.markdown(f"<h6 style='text-align: center;'><br><br>Choose a question to get started:</h6>", unsafe_allow_html=True)
      b0, b1, b2, b3, b4 = st.columns([1,1,1,1,1])
      with b1:
        if st.button("What is RAG in LLM?", use_container_width = True):
          st.session_state.question = "What is RAG in LLM?"
          st.session_state.button_clicked = True
          st.rerun()
          
      with b3:
        if st.button("What is Bag of Words?", use_container_width = True):
          st.session_state.question = "What is Bag of Words?"
          st.session_state.button_clicked = True
          st.rerun()
          
      with b2:
        if st.button("What is Recall in Machine Learning?", use_container_width = True):
          st.session_state.question = "What is Recall in Machine Learning?"
          st.session_state.button_clicked = True
          st.rerun()
  
  # Display the response 
  if st.session_state.question is not "":
      show_user_question(st.session_state.question, avatar_user)
      st.session_state.response = generate_conversational_response(st.session_state.question, collection)
      # st.chat_message("AI").write(st.session_state.response)
      show_ai_response(st.session_state.response,avatar_ai)
  
## Add feedback function


    # feedback = st.text_input("Was this answer helpful? Leave your feedback:")
    # if feedback:
    #     st.write("Thank you for your feedback!")
