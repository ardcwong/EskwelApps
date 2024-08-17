import streamlit as st
import openai
from openai import OpenAI
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from xhtml2pdf import pisa
from io import BytesIO
########################################################
# API KEYS and CREDENTIALS
########################################################
api_key = st.secrets["api"]['api_key']
openai.api_key = api_key
credentials = st.secrets["gcp_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
client = gspread.authorize(creds)
# Function to collect all markdowns into a single HTML content block
def collect_all_markdowns(markdowns):
    html_content = ""
    for sprint, sprint_markdown in markdowns.items():
        html_content += sprint_markdown
    return html_content
    
# Function to convert HTML content to PDF
def convert_html_to_pdf(html_content):
    # Embed CSS for margins
    # Embed CSS for scaling and margins
    html_with_styles = f"""
    <html>
    <head>
        <style>
            @page {{
                margin: 0.3in; /* Set margins */
            }}
            body {{
                transform: scale(0.5); /* Scale content */
                transform-origin: top left; /* Scale from top-left corner */
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    result = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_with_styles.encode("utf-8")), dest=result)
    if pisa_status.err:
        return None
    return result.getvalue()

# Google Sheets connection function
def google_connection_gsheet_courseoutline_ops(client):
    # Open the Google Sheet
    spreadsheet = client.open("Data Science Fellowship Curriculum")
    return spreadsheet

########################################################
# ACCESS Data Science Fellowship Curriculum GSHEET
########################################################
if "spreadsheet_courseoutline_ops" not in st.session_state:
    st.session_state.spreadsheet_courseoutline_ops = google_connection_gsheet_courseoutline_ops(client)


# Load CSV file containing the cohort's main topics and subtopics
def load_and_generate_course_outline(spreadsheet):
    worksheet = spreadsheet.worksheet("Data Science Fellowship Cohort")
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
  
  # df = pd.read_csv(filepath)
    course_outline = {}
    
    for _, row in df.iterrows():
        sprint = row['Sprint Number']
        main_topic = row['Main Topic']
        subtopic = row['Sub-Topics']
        
        if sprint not in course_outline:
            course_outline[sprint] = {}
        if main_topic not in course_outline[sprint]:
            course_outline[sprint][main_topic] = []
        course_outline[sprint][main_topic].append(subtopic)
    
    return course_outline

# Function to recommend five datasets for a specific sprint
def recommend_datasets(subtopic):
    query = f"""Recommend 5 datasets with links that are relevant for the subtopic '{subtopic}' for building a concrete deliverable. Provide dataset names, descriptions, use cases, and URLs.
    Ensure recommendations are presented in a standardized format:
    **[Dataset Name]**
        - **Description:** [Brief description of the dataset]
        - **Use Case:** [Relevant use cases for the dataset]
        - **URL:** [Dataset URL]
    """
    system_message = """You are a dataset recommendation assistant. 
    """
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ],
        max_tokens=900
    )
    datasets = response.choices[0].message.content.strip()
    return datasets
 # Use only <strong>, <br> to format your response. 
# Function to generate learning objectives for a specific sprint
def generate_learning_objectives(sprint, topics):
    query = f"Generate learning objectives for {sprint} based on the following topics: {topics}."
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a learning objectives assistant. Provide your response in JSON."},
            {"role": "user", "content": query}
        ],
        max_tokens=500
    )
    objectives = response.choices[0].message.content.strip()
    return objectives

#### TO REMOVE
# Function to retrieve and generates additional information about specific course topics
def generate_additional_content(query, collection):
    retrieved_docs = retrieve_documents(query, collection)
    context = ' '.join([doc['text'] for doc in retrieved_docs])
    
    prompt = f"Based on the following information:\n\n{context}\n\nAnswer the following question:\n{query}"
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that provides detailed educational content. "},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()

#### TO REMOVE
# Function to enhance course outline 
def enhance_course_outline(course_outline, collection):
    enhanced_outline = {}
    for sprint, topics in course_outline.items():
        enhanced_outline[sprint] = {}
        for main_topic, subtopics in topics.items():
            enhanced_outline[sprint][main_topic] = {}
            for subtopic in subtopics:
                query = f"Provide detailed information and educational content about {subtopic} in the context of {main_topic}."
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an assistant that provides detailed educational content."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500
                )
                additional_content = response.choices[0].message.content.strip()
                enhanced_outline[sprint][main_topic][subtopic] = additional_content
    return enhanced_outline

# Function to save the markdowns to the Google Sheet
def save_markdowns_to_gsheet(spreadsheet, sprint_markdowns, full_html_content):
    worksheet = spreadsheet.worksheet("Data Science Fellowship Cohort")
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Ensure that there is an "Enhanced Course Outline" column
    if "Enhanced Course Outline" not in df.columns:
        worksheet.update_cell(1, len(df.columns) + 1, "Enhanced Course Outline")
        df["Enhanced Course Outline"] = ""
    
    # Update the "Enhanced Course Outline" column for each sprint
    for sprint, markdown in sprint_markdowns.items():
        # Find the rows corresponding to the sprint
        rows = df[df['Sprint Number'] == sprint].index.tolist()
        for row in rows:
            worksheet.update_cell(row + 2, df.columns.get_loc("Enhanced Course Outline") + 1, markdown)

    cell = worksheet.find("Sprint 1", in_column=1)  # Assumes "Reference Number" is in the first column
    if cell:
        worksheet.update_cell(cell.row, worksheet.find("Full HTML_CONTENT").col, full_html_content)

    return True


if 'enhanced_course_outline' not in st.session_state:
    st.session_state.enhanced_course_outline = []
# Streamlit UI
st.title("Sprint Navigator")

st.markdown("""
The Sprint Navigator is a meticulously crafted course outline, designed to provide a clear and organized view of the program's main 
topics and sub-topics, learning objectives, divided into four distinct Sprints. It also offers tailored dataset recommendations for 
practical, hands-on learning. This Navigator acts as both a strategic planning tool and a detailed guide for fellows, helping them steer 
through their learning journey with confidence.
""")
# The Sprint Navigator is a meticulously crafted course outline, designed to provide a clear and organized view of the program's main topics and sub-topics, divided into four distinct Sprints. This Navigator acts as both a strategic planning tool and a detailed guide for fellows, helping them steer through their learning journey with confidence.

t1, t2 = st.columns([1,1])
if 'html_content_co' not in st.session_state:
    st.session_state.html_content_co = ""


with t2:
    with st.expander("Generate New Course Outline", expanded=True):
        # Initialize session state if it doesn't exist
        if 'markdowns' not in st.session_state:
            st.session_state['markdowns'] = {}
        if 'title' not in st.session_state:
            st.session_state.title = False
        AA, BB, CC = st.columns([2,1,1])
        with AA:
            

            if st.button("Generate New Course Outline", use_container_width = True):
                # Load and generate the course outline from the CSV file
                st.session_state.enhanced_course_outline = load_and_generate_course_outline(st.session_state.spreadsheet_courseoutline_ops)
                # st.session_state.enhanced_course_outline = enhance_course_outline(course_outline, None) #### TO UPDATE
                # datasets = recommend_datasets(subtopic)
                # learning_objectives = generate_learning_objectives(sprint, topics.keys())
            # Generate markdown for each sprint and save it in st.session_state
                for sprint, topics in st.session_state.enhanced_course_outline.items():
                    sprint_markdown = ""
                    for main_topic, subtopics in sorted(topics.items()):
                        # Add sprint and main topic to styled HTML markdown
                        sprint_markdown = f"""
                        <div style="border: 1px solid #1E73BE; border-radius: 5px; overflow: hidden; margin-bottom: 20px;">
                            <div style="background-color: #1E73BE; padding: 10px;">
                                <h4 style="color: white; margin: 0;">{sprint}: {main_topic}</h4>
                            </div>
                            <div style="background-color: #F8F9FA; padding: 15px;">
                        """
                        
                        # Add subtopics to the styled HTML markdown
                        subtopics_list = ', '.join(subtopics)
                        sprint_markdown += f"<p style='color: #333333;'><strong>Subtopics:</strong> {subtopics_list}<br></p>"
                
                        # Generate learning objectives and add to markdown
                        learning_objectives = generate_learning_objectives(sprint, list(topics.keys()))
                        # Convert the list of learning objectives into a numbered list in markdown format
                        numbered_list_learning_objectives = "\n".join(
                            [f"{i+1}. {obj}" for i, obj in enumerate(learning_objectives["learning_objectives"])]
                        )

                        
                        sprint_markdown += f"<p style='color: #333333;'><strong>Learning Objectives:</strong> {numbered_list_learning_objectives}<br></p>"
                        st.markdown(learning_objectives)
                        # Add recommended datasets for each subtopic to the styled HTML markdown
                        for subtopic in subtopics:
                            datasets = recommend_datasets(subtopic)
                            sprint_markdown += f"<p style='color: #333333;'><strong>Recommended Datasets:</strong> {datasets}<br></p>"
                
                        # Close the outer div
                        sprint_markdown += """
                            </div>
                        </div>
                        """
                    # Save the generated markdown in st.session_state
                    st.session_state['markdowns'][sprint] = sprint_markdown
                st.session_state.title = True
                st.rerun()
                # Loop through the sprints and topics to generate styled HTML markdown
        if st.session_state.title == True:
            st.markdown("""<h4 style='text-align: left;color: #e76f51;'><b>Course Outline</b></h4>""", unsafe_allow_html=True) 
        # # Example: Display the markdown for a specific sprint (Sprint 1)
        st.markdown(st.session_state['markdowns'].get('Sprint 1', ''), unsafe_allow_html=True)
        st.markdown(st.session_state['markdowns'].get('Sprint 2', ''), unsafe_allow_html=True)
        st.markdown(st.session_state['markdowns'].get('Sprint 3', ''), unsafe_allow_html=True)
        st.markdown(st.session_state['markdowns'].get('Sprint 4', ''), unsafe_allow_html=True)
        # st.write(st.session_state['markdowns'].get('Sprint 1', ''))
        # Collect all markdowns into a single HTML content block
        st.session_state.html_content_co = collect_all_markdowns(st.session_state['markdowns'])
        with BB:
            # Save markdowns to Google Sheet
            if st.session_state.html_content_co is not "":
                if st.button("Update", use_container_width = True):
                    saved_ = save_markdowns_to_gsheet(st.session_state.spreadsheet_courseoutline_ops, st.session_state['markdowns'],st.session_state.html_content_co)
                    if saved_:
                        st.success("HTML content saved successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to save HTML content.")
        

        
        with CC:
            if st.session_state.html_content_co is not "":
                pdf = convert_html_to_pdf(st.session_state.html_content_co)
                if pdf:
                    st.download_button(label=f"Download PDF", data=pdf, file_name="Course_Outline.pdf", mime="application/pdf", use_container_width = True)
                else:
                    st.error("Failed to convert HTML to PDF.")

with t1:
    if 'get_current_markdown_co' not in st.session_state:
        st.session_state.get_current_markdown_co = ""
    
    def load_course_outline_dataset(spreadsheet):
        worksheet = spreadsheet.worksheet("Data Science Fellowship Cohort")
        data_score = worksheet.get_all_values()
        df_co = pd.DataFrame(data_score[1:], columns=data_score[0])
        return df_co


    df_co = load_course_outline_dataset(st.session_state.spreadsheet_courseoutline_ops)
    get_current_markdown = ""
    with st.expander("Current Course Outline", expanded=True):
        
        for i in range(4):
            get_current_markdown +=  df_co[df_co['Sprint Number'] == f"Sprint {i+1}"]['Enhanced Course Outline'].values[0]
            # st.session_state.get_current_markdown += get_current_markdown
        st.session_state.get_current_markdown_co = df_co[df_co['Sprint Number'] == f"Sprint 1"]['Full HTML_CONTENT'].values[0]    
            
        # st.markdown(st.session_state.get_current_markdown, unsafe_allow_html=True)     
        pdf_current = convert_html_to_pdf(st.session_state.get_current_markdown_co)
        if pdf_current:
            st.download_button(label=f"Download PDF (Current CO)", data=pdf_current, file_name="Course_Outline.pdf", mime="application/pdf", use_container_width = True)
        else:
            st.error("Failed to convert HTML to PDF.")

        st.markdown("""<h4 style='text-align: left;color: #e76f51;'><b>Course Outline</b></h4>""", unsafe_allow_html=True) 
        
        for i in range(4):
            st.markdown(df_co[df_co['Sprint Number'] == f"Sprint {i+1}"]['Enhanced Course Outline'].values[0], unsafe_allow_html=True)
            
            
