import streamlit as st
import requests
import io
import base64
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #009688, #3F51B5);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-family: Arial, sans-serif;
        color: white;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
    ">
        <h1 style="font-size: 40px; margin-bottom: 10px; font-weight: bold; letter-spacing: 2px; color: white;">
            Installation Guide
        </h1>
    </div>
    """,
    unsafe_allow_html=True)
st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
# st.markdown(
#     "<h2 style='text-align: left; color: #48a937; font-size: 35px;'>Installation Guide</h2>",
#     unsafe_allow_html=True
# )

choose_mac = "Installation Guide for MAC OS"
pdf_url_mac = "https://drive.google.com/uc?export=download&id=1kBWygtPP5nkzCv9uR3AX2Y-PGjCFpeFr"
youtube_url_mac = "https://www.youtube.com/watch?v=2xh5sjpAI6k"

choose_windows = "Installation Guide for Windows"
pdf_url_windows = "https://drive.google.com/uc?export=download&id=1bNYZP591fY5-rwjKbSYHAUuNjmYsqV9N"
youtube_url_windows = "https://www.youtube.com/watch?v=UTqOXwAi1pE"

choose_python = "How to Run Python in Anaconda"
pdf_url_python = "https://drive.google.com/uc?export=download&id=18DltGgOgzL3gbqlFCGxqG581g8fkFkHu"
youtube_url_python = "https://www.youtube.com/watch?v=DPi6CAkUUPY"

if 'yt_link' not in st.session_state:
    st.session_state.yt_link = youtube_url_mac

if 'choose' not in st.session_state:
    st.session_state.choose = choose_mac

if 'pdf' not in st.session_state:
    st.session_state.pdf = pdf_url_mac

colA, colB = st.columns([1,2])
with colA:
    with st.expander("Anaconda", expanded=True):
        st.image('data/anaconda.png', use_column_width = True)
    # st.markdown(f"<h1 style='text-align: center;'> Installation Guide </h1>", unsafe_allow_html=True)
    with st.expander("What do we have here", expanded=True):
        st.markdown(
        """
        <p style='text-align: center; color: #333333; font-size: 20px;'>
            Welcome to the installation guide where you'll find all the necessary steps 
            to set up your environment and get started with the installation process of Anaconda.
        </p>
        """,
        unsafe_allow_html=True
        )
    with st.expander("Choose", expanded=True):
        
        with st.container():
            a, b = st.columns([1,2])
            with a:
                
                st.image('data/apple.png')
            with b:
                st.subheader("MAC OS")
                # st.markdown("<h4 style='text-align: left;'>MAC OS</h4>", unsafe_allow_html=True)
                st.markdown("***Install on your MAC OS***")
                if st.button("Watch", use_container_width=True, type = "primary", help = "Click to Watch Installation Guide for MAC OS"):
                    st.session_state.choose = choose_mac
                    st.session_state.yt_link = youtube_url_mac
                    st.session_state.pdf = pdf_url_mac
                    
        
        with st.container():
            c, d = st.columns([1,2])
            with c:
                
                st.image('data/windows.png')
            with d:
                st.subheader("Windows")
                # st.markdown("<h2 style='text-align: center;'>MAC OS</h2>", unsafe_allow_html=True)
                st.markdown("***Install on your Windows***")
                if st.button("Watch", use_container_width=True, type = "primary", help = "Click to Watch Installation Guide for Windows"):
                    st.session_state.choose = choose_windows
                    st.session_state.yt_link = youtube_url_windows      
                    st.session_state.pdf = pdf_url_windows

        with st.container():
            e, f = st.columns([1,2])
            with e:
                
                st.image('data/python.png')
            with f:
                st.subheader("Run Python")
                # st.markdown("<h2 style='text-align: center;'>MAC OS</h2>", unsafe_allow_html=True)
                st.markdown("***Run Python in Anaconda***")
                if st.button("Watch", use_container_width=True, type = "primary", help = "Click to Watch Run Python in Anaconda"):
                    st.session_state.choose = choose_python
                    st.session_state.yt_link = youtube_url_python  
                    st.session_state.pdf = pdf_url_python

def yt_video():
    return st.video(st.session_state.yt_link)
    
def download_pdf(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    return save_path

def pdf_view():
    pdf_url = st.session_state.pdf
    local_pdf_path = f"/tmp/{st.session_state.choose}.pdf"

    # Download the PDF from the URL
    downloaded_pdf = download_pdf(pdf_url, local_pdf_path)
    return local_pdf_path, downloaded_pdf

with colB:
    with st.expander(f"Video", expanded=True):
        st.subheader(f"Watch Youtube Video: {st.session_state.choose}")
        yt_video()
        
    with st.expander("PDF", expanded=True):
        
        local_pdf_path, downloaded_pdf = pdf_view()
        # Provide a download button for the PDF
        if downloaded_pdf:
            with open(downloaded_pdf, "rb") as file:
                pdf_col_1, pdf_col_2 = st.columns([8,2])
                with pdf_col_1:
                    st.subheader(f"Read: {st.session_state.choose}")
                with pdf_col_2:
                    st.download_button(
                        label="Download PDF",
                        data=file,
                        file_name=f"{st.session_state.choose}.pdf",
                        mime="application/pdf",
                        use_container_width = True,
                        type = "primary"
                    )
        if local_pdf_path:
            with st.container(height = 600):
                # Display the PDF using pdf_viewer
                pdf_viewer(local_pdf_path)   



# col1, col2, col3 = st.columns(3)

# with col1:
#     st.markdown("<h2 style='text-align: center;'>MAC OS</h2>", unsafe_allow_html=True)
#     st.markdown("***Install on your MAC OS***")
#     st.image('data/apple.png')

# with col2:
#     st.markdown("<h2 style='text-align: center;'>WINDOWS</h2>", unsafe_allow_html=True)
#     st.markdown("***Install on your Windows***")
#     st.image('data/windows.png')

# with col3:
#     st.markdown("<h2 style='text-align: center;'>RUN PYTHON</h2>", unsafe_allow_html=True)
#     st.markdown("***Run Python in Anaconda***")
#     st.image('data/python.png')

# def fetch_pdf_content(url):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         return response.content
#     except requests.exceptions.RequestException as e:
#         st.error(f"An error occurred: {e}")
#         return None



# col4, col5, col6 = st.columns(3)

# with col4:
#     st.markdown(
#             """
#             <a href="https://www.youtube.com/watch?v=2xh5sjpAI6k" target="_blank">
#                 <button style="background-color:#FF4B4B;color:white;padding:10px 20px;border:none;border-radius:5px;">
#                     Youtube Video Installation Guide
#                 </button>
#             </a>
#             """,
#             unsafe_allow_html=True
#         )

#     st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
#     #May isa pang button to proceed with download
#     if st.button('PDF Guide for MAC OS', type="primary", use_container_width=True):
#         pdf_content = fetch_pdf_content(pdf_url_mac)
#         if pdf_content:
#             st.download_button(
#                 label="Download PDF",
#                 data=pdf_content,
#                 file_name='MAC OS_Installation Guide.pdf',
#                 mime='application/pdf'
#             )
            
#     # # # Direct download once clicked
#     # # with col4:
#     # if st.button('Download Installation Guide for MAC OS', type="primary", use_container_width=True):
#     #     pdf_content_mac = fetch_pdf_content(pdf_url_mac)
        
#     # if pdf_content_mac:
#     #     st.download_button(
#     #         label='Download Installation Guide for MAC OS',
#     #         data=pdf_content_mac,
#     #         file_name='MAC_OS_Installation_Guide.pdf',
#     #         mime='application/pdf'
#     #     )

# with col5:
#     st.markdown(
#             """
#             <a href="https://www.youtube.com/watch?v=UTqOXwAi1pE" target="_blank">
#                 <button style="background-color:#FF4B4B;color:white;padding:10px 20px;border:none;border-radius:5px;">
#                     Youtube Video Installation Guide 
#                 </button>
#             </a>
#             """,
#             unsafe_allow_html=True
#         )

#     st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

#     if st.button('PDF Guide for Windows', type="primary", use_container_width=True):
#         pdf_content = fetch_pdf_content(pdf_url_windows)
#         if pdf_content:
#             st.download_button(
#                 label="Download PDF",
#                 data=pdf_content,
#                 file_name='Windows_Installation Guide.pdf',
#                 mime='application/pdf'
#             )

# with col6:

#     st.markdown(
#             """
#             <a href="https://www.youtube.com/watch?v=DPi6CAkUUPY" target="_blank">
#                 <button style="background-color:#FF4B4B;color:white;padding:10px 20px;border:none;border-radius:5px;">
#                     Youtube Video Installation Guide
#                 </button>
#             </a>
#             """,
#             unsafe_allow_html=True
#         )

#     st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
#     if st.button('PDF Guide to Run Python', type="primary", use_container_width=True):
#         pdf_content = fetch_pdf_content(pdf_url_run)
#         if pdf_content:
#             st.download_button(
#                 label="Download PDF",
#                 data=pdf_content,
#                 file_name='Run Python_Installation Guide.pdf',
#                 mime='application/pdf'
#             )


