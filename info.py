import streamlit as st
from pathlib import Path
from PIL import Image
import base64

PAGE_TITLE = "Digital CV | Tan Le"
PAGE_ICON = ":wave:"
NAME = "TAN LE SI"
DESCRIPTION = """
Bachelor student with experience of data analysing, searching for data-driven bachelor thesis 
"""
EMAIL_ADDRESS = "tan.lesi@study.hs-duesseldorf.de"
DATE_OF_BIRTH = "31 May 1997"
LOCATION = "Essen, Germany"
LINKEDIN = "https://www.linkedin.com/in/tan-le-si-558a06212/"
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout= 'wide')

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'


def two_col_txt(a, b, ratio: list):
  col1, col2 = st.columns(ratio)
  with col1:
    st.write(a)
  with col2:
    st.write(b)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


img_col, info_col = st.columns([2,3])

with img_col:
    st.image(Image.open(IMAGE_FOLDER/ 'Bewerbungsfoto.jpg'), width= 230)
    st.title(NAME)
    st.write("📅", DATE_OF_BIRTH)
    st.write("📍", LOCATION)
    st.write("📧", EMAIL_ADDRESS)
    st.write(f"""🔗 <a href={LINKEDIN}>LinkedIn</a>""", unsafe_allow_html= True)
with info_col:
    st.write("# About Me")
    st.markdown("""
        <div>
        <ul class="listBig">
            <p style="margin-bottom: 20px;"><li class= "listBig"> I'm a bachelor student from Hochschule Düsseldorf, searching for a data-driven bachelor thesis to complete my degree.</li></p>
            <p style="margin-bottom: 20px;"><li class= "listBig"> I'm enthusiastic about finding insights and patterns from large datasets, based on which strategical decisions will be made.</li></p>
            <li class= "listBig"> I have 15 months experience of utilizing Python and SQL for data analysing and visualising purposes.</li>
        </ul>
        </div>
    """, unsafe_allow_html= True)
    with open(f"{CURRENT_DIR/'assets'/'Lebenslauf.pdf'}", 'rb') as f:
        data = f.read()
        bin_str = base64.b64encode(data).decode()
    st.markdown("<br>",unsafe_allow_html=True)
    st.write(f"""
        <div style="text-align:center;">
        <a href="data:application/octet-stream;base64,{bin_str}" download="Lebenslauf_Tan_Le.pdf">
            <button class="downloadButton" type="button">Download my CV here</button>
        </a></div>
    """, unsafe_allow_html= True)

st.markdown("<hr>",unsafe_allow_html=True)
# --- Education ---
st.write('\n')
st.header("Education")
two_col_txt("##### Bachelor of Engineer, 🔗 [Hochschule Düsseldorf, Germany](https://mv.hs-duesseldorf.de/)", "##### 09/2018-now", ratio=[4,1])

with open(f"{CURRENT_DIR/'assets'/'GPA.pdf'}", 'rb') as f:
    data = f.read()
    bin_str = base64.b64encode(data).decode()
    GPA_href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="GPA_Tan_Le.pdf">Current GPA: 1.8</a>'

st.write(f"""
    - Major: Mechanical engineering, production technology
    - 🔗 {GPA_href}
""", unsafe_allow_html= True)


st.markdown("<hr>",unsafe_allow_html=True)
# --- Work experience ---

st.write('\n')
st.header("Work Experience")

two_col_txt("##### Backend Developer/ Data Analyst", "##### 09/2021-now", ratio=[4,1])
st.write("🔗 [Perixx Ltd., Düsseldorf, Germany](https://www.linkedin.com/company/perixx-computer-gmbh/)")
st.write("""
        - Functionality development for an internal ERP web application\n
        - Data analysing and visualisation for controlling inventory/sales of large number of products\n
        - Working with API to gather data from Amazon server
        - Automate daily and bulk office tasks with Python
    """)

st.write("\n")
st.write("\n")
two_col_txt("##### Tutor for Scientific Computing", "##### 09/2022-now", ratio=[4,1])
st.write("🔗 [Hochschule Düsseldorf, Germany](https://mv.hs-duesseldorf.de/)")
st.write("""
        - Assisting students with familiarizing the usage of Matlab \n
        - Applying Matlab to mechanical related numerical calculations\n
    """)

st.markdown("<hr>",unsafe_allow_html=True)
# --- Skills  ---

st.write('\n')
st.header("Skills")
two_col_txt("Programming", "Python, Linux, SQL, Matlab",ratio= [2,2])
two_col_txt("Data collecting/processing", "SQL, pandas",ratio= [2,2])
two_col_txt("Data visualising", "Python, streamlit, plotly",ratio= [2,2])

st.markdown("<hr>",unsafe_allow_html=True)
# --- Languages  ---

st.write('\n')
st.header("Languages")
two_col_txt("English", "Fluent",ratio= [2,2])
two_col_txt("Deutsch", "Fluent",ratio= [2,2])
two_col_txt("Vietnamese", "First language",ratio= [2,2])

st.markdown("<hr>",unsafe_allow_html=True)
# --- Portfolio  ---

st.write('\n')
st.header("Portfolio")
st.write("Navigate through the side tabs to view my portfolio")
