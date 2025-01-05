import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredURLLoader
import yt_dlp

def extract_youtube_content(url):
    ydl_opts = {'format': 'bestaudio/best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        description = info.get('description', 'No description available.')
        title = info.get('title', 'No title available.')
        return f"Title: {title}\n\nDescription: {description}"

st.set_page_config(page_title="Summarize & Q/A from YT or URL", page_icon="")
st.title("Summarize & Q/A from YT or URL")
st.subheader("Summarize & Ask Questions")

GROQ_API_KEY = "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"

generic_url = st.text_input("Enter URL (YouTube or Website)", label_visibility="collapsed")

llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)

prompt_template = """
Provide a summary of the following content in 300 words:
Content:{text}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

if "docs" not in st.session_state:
    st.session_state.docs = None
if "summary" not in st.session_state:
    st.session_state.summary = None

if st.button("Summarize the Content from YT or Website"):
    if not generic_url.strip():
        st.error("Please provide the URL.")
    elif not validators.url(generic_url):
        st.error("Please enter a valid URL. It can be a YouTube video URL or a website URL.")
    else:
        try:
            with st.spinner("Processing..."):
                if "youtube.com" in generic_url or "youtu.be" in generic_url:
                    try:
                        from langchain_community.document_loaders import YoutubeLoader
                        loader = YoutubeLoader.from_youtube_url(generic_url, add_video_info=True)
                        docs = loader.load()
                    except Exception as yt_error:
                        content = extract_youtube_content(generic_url)
                        docs = [Document(page_content=content)]
                else:
                    loader = UnstructuredURLLoader(urls=[generic_url])
                    docs = loader.load()

                chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
                summary = chain.run(docs)

                st.session_state.docs = docs
                st.session_state.summary = summary

                st.success(summary)

        except Exception as e:
            st.exception(f"Exception: {e}")

if st.session_state.docs:
    st.subheader("Ask Questions")
    user_question = st.text_input("Enter your question about the content:")
    if st.button("Get Answer"):
        if not user_question.strip():
            st.error("Please enter a question.")
        else:
            try:
                with st.spinner("Processing your question..."):
                    qa_chain = load_qa_chain(llm, chain_type="stuff")
                    answer = qa_chain.run(input_documents=st.session_state.docs, question=user_question)
                    st.success(answer)
            except Exception as e:
                st.exception(f"Exception: {e}")
