import streamlit as st
from extractor import SectionExtractor
from agent import DocQAAgent

st.title("💬 Agentic DocQA")
st.caption("🚀 A Streamlit DocQA Chatbot powered by Smolagent + OpenAI")

uploaded_file = st.file_uploader("Upload your document", type=["pdf", "txt", "docx"])



if uploaded_file is not None:
    if "ingested" not in st.session_state:
        file_extension = uploaded_file.name.split(".")[-1]
            
        # Save the uploaded file temporarily
        temp_path = f"temp.{file_extension}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Extract text from the document
        if file_extension == 'pdf' or file_extension == "txt" or file_extension == "docx":
            pass
        else:
            st.error("Unsupported file format")
            st.stop()

        st.write("Ingesting Document...")

        with st.spinner("Processing documents... please wait"):
            sectionExtractor = SectionExtractor(temp_path)
            sections = sectionExtractor.process()
            docQAAgent = DocQAAgent()
            docQAAgent.setSections(sections)
            st.session_state["agent"] = docQAAgent
                               
        st.success("Document Ingestion complete!")
        st.session_state["ingested"] = True
    
            

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
    
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    docQAAgent = st.session_state["agent"]
    
    with st.spinner("Generating response..."):
        msg = docQAAgent.run(prompt)
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)