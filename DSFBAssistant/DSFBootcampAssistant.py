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
  openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=openai.api_key, model_name="text-embedding-ada-002")
  try:
    collection = client_chromadb_2.get_or_create_collection(
      name=COLLECTION_NAME_2,
      embedding_function=openai_ef,
      metadata={"hnsw:space": "cosine"}
    )
    return collection
  except:
    st.error("error")
    return None


collection = load_collection_DSFBAssistant()


def return_best_eskdata(user_input, collection, n_results=1):
    query_result = collection.query(query_texts=[user_input], n_results=n_results)
    if not query_result['ids'] or not query_result['ids'][0]:
        return None, None
    top_result_id = query_result['ids'][0][0]
    top_result_metadata = query_result['metadatas'][0][0]
    top_result_document = query_result['documents'][0][0]
    return top_result_metadata.get('eskdata', 'Unknown Data'), top_result_document

def generate_conversational_response_DSFBAssistant(user_input, collection):
    relevant_name, relevant_document = return_best_eskdata(user_input, collection)
    if not relevant_name:
        return "I couldn't find any relevant articles based on your input."
    messages = [
        {"role": "system", "content": "You are a bot that makes recommendations for each Sprint 1 to 4 for the Data Science bootcamp."},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": f"This is the recommended article: {relevant_name}. Here is a brief about the article: {relevant_document}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("Data Science Bootcamp Assistant")
st.write("Ask any question related to the bootcamp, and get recommendations and answers.")

user_input = st.text_input("Enter your question:")
if user_input:
    response = generate_conversational_response_DSFBAssistant(user_input, collection)
    st.write(response)
