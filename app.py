import streamlit as st
from Scripts.prompt import ask

st.set_page_config(page_title="SEC 10-K RAG", page_icon="📊")
st.title("📊 SEC 10-K RAG Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about SEC filings..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask(prompt)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})