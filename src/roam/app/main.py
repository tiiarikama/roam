import streamlit as st
from roam.rag.chain import ask

WELCOME_MESSAGE = (
    "Welcome to Roam! I can help you plan trips to US national parks. "
    "Ask me about trails, permits, campgrounds, road conditions, and more. "
    "Which park are you interested in?"
)


st.set_page_config(page_title="Roam - Plan Your Next Adventure", page_icon="static/favicon.png")

col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.image("static/logo.svg", use_column_width=True)

# resets chat history and empties previously used park codes
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]
    st.session_state.last_park_codes = []
    st.rerun()

# initializes session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

if "last_park_codes" not in st.session_state:
    st.session_state.last_park_codes = []

# displays chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# handles user query
query = st.chat_input("Ask about a national park...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, park_codes = ask(
                query,
                history=st.session_state.messages[:-1],
                last_park_codes=st.session_state.last_park_codes,
            )
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    if park_codes:
        st.session_state.last_park_codes = park_codes
