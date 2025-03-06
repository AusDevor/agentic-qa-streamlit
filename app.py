import streamlit as st
from streamlit_tags import st_tags
from extractor import SectionExtractor
from agent import DocQAAgent
from extract_doc import *
from chatbot import *
import time
import asyncio
import streamlit_authenticator as stauth

colAgent, colLegacy = None, None

def get_file_list ():
    if 'file_list' not in st.session_state:
        st.session_state['file_list'] = []
    return st.session_state['file_list']
    
def get_agent ():
    if 'agent' not in st.session_state:
        st.session_state['agent'] = DocQAAgent()
    return st.session_state['agent']

def get_agent_messages ():
    if 'agent_messages' not in st.session_state:
        st.session_state['agent_messages'] = [{"role": "assistant", "content": "How can I help you?"}]
    return st.session_state['agent_messages']

def get_legacy_messages ():
    if 'legacy_messages' not in st.session_state:
        st.session_state['legacy_messages'] = [{"role": "assistant", "content": "How can I help you?"}]
    return st.session_state['legacy_messages']

def get_agent ():
    if 'agent' not in st.session_state:
        st.session_state['agent'] = DocQAAgent([])
    return st.session_state['agent']
    
def set_agent (agent):
    st.session_state['agent'] = agent
    

@st.dialog("Upload Documents")
def uploadDocument():
    uploaded_file = st.file_uploader("Click to import, or drag and drop here PDF or TXT or DOC/DOCX", type=["pdf", "txt", "doc", "md", "docx"])

    if uploaded_file is not None:
        file_path = uploaded_file.name
        file_extension = uploaded_file.name.split(".")[-1]
            
        # Save the uploaded file temporarily
        temp_path = f"temp/{file_path}"
        buf = uploaded_file.getbuffer()
        if file_extension == 'pdf' or file_extension == 'docx' or file_extension == "md" or file_extension == "txt":
            with open(temp_path, 'wb') as file:
                file.write(buf)
        
        elif file_extension == 'doc':
            text = extract_doc(bytes(buf))
            with open(temp_path, 'w') as file:
                file.write(text)
        
        else:
            st.error("Unsupported file format")
            st.stop()
            

        st.write("Ingesting Document...")
        

        # Extract Sections from file content for ingestion
        with st.spinner("Processing documents... please wait (Agentic)"):
            sectionExtractor = SectionExtractor(file_path)
            sections = asyncio.run(sectionExtractor.process())
            
            print (sections)
            set_agent (DocQAAgent(get_agent().sections + sections))
            print("Section Count", len(get_agent().sections))
            
        success_bar = st.empty()
        st.success("Document Ingestion complete! (Agentic)")
        time.sleep(0.1)
        success_bar.empty()
                
        with st.spinner("Processing documents... please wait (Legacy)"):
            files=[
                ('files',(file_path,open(temp_path,'rb')))
            ]
            addFile(files)
                            
        # Display Success Status    
        success_bar = st.empty()
        st.success("Document Ingestion complete! (Legacy)")
        time.sleep(0.1)
        success_bar.empty()
        
        get_file_list().append(file_path)
        
        st.rerun()
        
    
    
##################################################################################################################
#############################################       UI(AUTH)       ###############################################
##################################################################################################################

st.set_page_config(layout="wide")  # Enables full-width layout

config = {
    'credentials': {
        'usernames': {
            'qa': {'email': 'qa@johnsnowlabs.com', 'name': 'QA', 'password': 'jsl@PA'},
        },
    },
    'cookie': {'expiry_days': 30, 'key': 'some_secret_key', 'name': 'streamlit_auth'}
}

authenticator = stauth.Authenticate (
    config ['credentials'],
    config ['cookie']['name'],
    config ['cookie']['key'],
    config ['cookie']['expiry_days'],
)

authenticator.login(location='main')

authentication_status = st.session_state.get('authentication_status')

if authentication_status is False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status is None:
    st.warning('Please enter your crendentials')
    st.stop()
    
##################################################################################################################
#############################################       UI(MAIN)       ###############################################

colAgentTitle, colLegacyTitle = st.columns(2)

if st.button("Add File for DocQA", use_container_width=True):
    uploadDocument()
        
keywords = st_tags(
    label='Target Documents:',
    text='',
    value=get_file_list(),
    maxtags=100,
    key="tag_files_" + str(len(get_file_list()))
)

colAgent, colLegacy = st.columns(2)

colAgentTitle.title("💬 Agentic DocQA")
colAgentTitle.caption("Agentic Chatbot powered by Smolagent + OpenAI")

colLegacyTitle.title("💬 Legacy DocQA")
colLegacyTitle.caption("Legacy Chatbot powered by Semantic Search")

for msg in get_agent_messages():
    colAgent.chat_message(msg["role"]).write(msg["content"])
    
for msg in get_legacy_messages():
    colLegacy.chat_message(msg["role"]).write(msg["content"])
    
if prompt := st.chat_input():

    st.session_state["agent_messages"].append({"role": "user", "content": prompt})
    st.session_state["legacy_messages"].append({"role": "user", "content": prompt})
    colAgent.chat_message("user").write(prompt)
    colLegacy.chat_message("user").write(prompt)
    
    docQAAgent = get_agent()
    
    with st.spinner("Generating response..."):
        msg_agent = docQAAgent.run(prompt)
        msg_legacy = get_answer(prompt)
        
    st.session_state["agent_messages"].append({"role": "assistant", "content": msg_agent})
    st.session_state["legacy_messages"].append({"role": "assistant", "content": msg_legacy})
    colAgent.chat_message("assistant").write(msg_agent)
    colLegacy.chat_message("assistant").write(msg_legacy)