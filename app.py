import streamlit as st
from streamlit_tags import st_tags
from extractor import SectionExtractor
from agent import DocQAAgent
from extract_doc import *
from chatbot import *
import time
import random
import string

st.set_page_config(layout="wide")  # Enables full-width layout


colAgent, colLegacy = st.columns(2)


colAgent.title("💬 Agentic DocQA")
colAgent.caption("Agentic Chatbot powered by Smolagent + OpenAI")

colLegacy.title("💬 Legacy DocQA")
colLegacy.caption("Legacy Chatbot powered by Semantic Search")

    
        
@st.dialog("Upload Documents")
def uploadDocument(mode="agent"):
        
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
        with st.spinner("Processing documents... please wait"):
            
            if mode == "agent":
                sectionExtractor = SectionExtractor(file_path)
                sections = sectionExtractor.process()
                docQAAgent = DocQAAgent()
                docQAAgent.setSections(sections)
                
                if "agent" not in st.session_state:
                    st.session_state["agent"] = docQAAgent
                    print(len(st.session_state["agent"].sections))
                else:
                    prev_sections = st.session_state["agent"].sections
                    
                    st.session_state["agent"].setSections(prev_sections + sections)
                    print(len(st.session_state["agent"].sections))
            
            else:
                files=[
                    ('files',(file_path,open(temp_path,'rb')))
                ]
                addFile(files)
                            
        # Display Success Status    
        success_bar = st.empty()
        st.success("Document Ingestion complete!")
        time.sleep(0.1)
        success_bar.empty()
        
        files_field = f'{mode}_files'
        
        if files_field in st.session_state:
            st.session_state[files_field].append(file_path)
        else:
            st.session_state[files_field] = [file_path]
        
        st.rerun()
        
        

if colAgent.button("Add File for Agentic DocQA"):
    uploadDocument(mode="agent")
    
if colLegacy.button("Add File for Legacy DocQA"):
    uploadDocument(mode="legacy")
    

fileList1 = []    
if 'agent_files' in st.session_state:
    fileList1 = st.session_state['agent_files']
    
with colAgent:
    keywords = st_tags(
        label='Target Documents:',
        text='',
        value=fileList1,
        maxtags=10,
        key="tag_agent_files_" + str(len(fileList1))
    )
   
fileList2 = [] 
if 'legacy_files' in st.session_state:
    fileList2 = st.session_state['legacy_files']


with colLegacy:
    keywords = st_tags(
        label='Target Documents:',
        text='',
        value=fileList2,
        maxtags=10,
        key="tag_legacy_files_" + str(len(fileList2))
    )



if "messages" not in st.session_state:
    st.session_state["agent_messages"] = [{"role": "assistant", "content": "How can I help you?"}]
    st.session_state["legacy_messages"] = [{"role": "assistant", "content": "How can I help you?"}]
    
for msg in st.session_state["agent_messages"]:
    colAgent.chat_message(msg["role"]).write(msg["content"])
    
for msg in st.session_state["legacy_messages"]:
    colLegacy.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():

    st.session_state["agent_messages"].append({"role": "user", "content": prompt})
    st.session_state["legacy_messages"].append({"role": "user", "content": prompt})
    colAgent.chat_message("user").write(prompt)
    colLegacy.chat_message("user").write(prompt)
    
    docQAAgent = st.session_state["agent"]
    
    with st.spinner("Generating response..."):
        msg_agent = docQAAgent.run(prompt)
        msg_legacy = get_answer(prompt)
        
    st.session_state["agent_messages"].append({"role": "assistant", "content": msg_agent})
    st.session_state["legacy_messages"].append({"role": "assistant", "content": msg_legacy})
    colAgent.chat_message("assistant").write(msg_agent)
    colLegacy.chat_message("assistant").write(msg_legacy)
    
    