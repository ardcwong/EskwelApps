import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import openai
import base64

########################################################
# PAGE CONFIG
########################################################
st.set_page_config(
    page_title = "Welcome to Eskwelabs App!",
    initial_sidebar_state="expanded",
    layout='wide',
    menu_items={
    'About': "### Hi! Thanks for viewing our app!"
    }
)


########################################################
# LOAD STYLES CSS
########################################################
# Function to load local CSS file
def load_local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            # st.success("CSS loaded successfully!")  # Debug statement
    except FileNotFoundError:
        st.error(f"File {file_name} not found!")

#Load the local CSS file from the 'data' directory
load_local_css("data/styles.css")



########################################################
# CHANGE BACKGROUND USING LOCAL PNG
########################################################
@st.cache(allow_output_mutation=True)
def set_bg_hack(main_bg):
    '''
    A function to unpack an image from root folder and set as bg.
 
    Returns
    -------
    The background.
    '''
    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

set_bg_hack('data/bg.png')


########################################################
# API KEYS and CREDENTIALS
########################################################
api_key = st.secrets["api"]['api_key']
openai.api_key = api_key
credentials = st.secrets["gcp_service_account"]


########################################################
# SUITABILITY
########################################################
@st.fragment
def suitability():
    # Define the questions
    questions = [
        "What is your highest level of education completed?",
        "Do you have any prior experience in programming or data analysis? If yes, please describe.",
        "Do you prefer structured learning environments with a clear curriculum, or do you thrive in self-paced, unstructured settings?",
        "How many hours per week can you realistically dedicate to learning data science?",
        "What are your long-term career goals in the field of data science?"
    ]
    
    # Streamlit app setup
    st.title("Data Science Learning Path Classifier")
    st.write("Please answer the following questions to determine your suitability for different learning paths in data science.")
    
    # Initialize or retrieve session state
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'question_index' not in st.session_state:
        st.session_state.question_index = 0
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # # Display the entire chat history
    # for role, message in st.session_state.chat_history:
    #     st.chat_message(role).write(message)
    # Display the entire chat history with user responses on the right
    for role, message in st.session_state.chat_history:
        st.chat_message(role).write(message)
    
    # Function to display the current question and collect user response
    def display_question():
        if st.session_state.question_index < len(questions):
            current_question = questions[st.session_state.question_index]
            st.chat_message("AI").write(current_question)
            user_response = st.chat_input("Your response:")
            if user_response:
                st.session_state.responses.append(user_response)
                st.session_state.chat_history.append(("AI", current_question))
                st.session_state.chat_history.append(("User", user_response))
                st.session_state.question_index += 1
                st.rerun(scope="fragment")
    
    # Function to get classification from OpenAI
    def get_classification():
        questions_responses = ""
        for i, question in enumerate(questions):
            questions_responses += f"{i+1}. {question}\n   - Response: {st.session_state.responses[i]}\n"
    
        prompt = f"""
        Classify the following person’s suitability for a data science bootcamp, self-learning, or a master's program based on their responses to the questions:
        {questions_responses}
        Suitability:
        """
    
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies education suitability."},
                    {"role": "user", "content": prompt}
                ]
            )
            classification = response.choices[0].message.content.strip()
            return classification
        except Exception as e:
            st.error(f"Error: {e}")
            return None
    
    # Main logic
    if st.session_state.question_index < len(questions):
        display_question()
    else:
        if st.session_state.responses and st.session_state.question_index == len(questions):
            classification = get_classification()
            if classification:
                st.session_state.chat_history.append(("Suitability", classification))
                st.session_state.question_index += 1
                st.rerun(scope="fragment")

            # with st.container(border=True):
        #     suitability()    

############################
# RUN SUITABILITY
############################
suitability()

