import streamlit as st
from roam.rag.chain import ask

WELCOME_MESSAGE = {
            "role": "assistant",
            "content": (
                "Welcome to Roam! I can help you plan trips to US national parks. "
                "Ask me about trails, permits, campgrounds, road conditions, and more. "
                "Which park are you interested in?"
            ),
        }

st.set_page_config(page_title="Roam - Plan Your Next Adventure", page_icon="static/favicon.png")

col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.image("static/logo.svg", use_column_width=True)

if st.button("Reset Chat"):
    st.session_state.messages = [WELCOME_MESSAGE]
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [WELCOME_MESSAGE]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask about a national park...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask(query)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
