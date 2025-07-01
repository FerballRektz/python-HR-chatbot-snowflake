import streamlit as st
import yaml
import streamlit_functions_langchain
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import START, StateGraph
import os

# ------------------ PAGE CONFIG + STYLING ------------------
st.set_page_config(page_title="🗨️ AskHR", layout="centered")

st.markdown(
    """
    <style>
    .main {
        background-color: #f0f0f0;
    }
    .block-container {
        padding-top: 8rem; /* Push content lower */
    }
    .chatbot-banner {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: white;
        border-radius: 12px;
        padding: 20px 30px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.1);
        z-index: 999;
        text-align: center;
        width: max-content;
    }
    .chatbot-banner h1 {
        color: #1E90FF;
        font-size: 36px; /* bigger title */
        font-weight: 800;
        margin: 0;
    }
    .chatbot-banner p {
        font-size: 18px;  /* bigger subtitle */
        color: #555;
        margin: 4px 0 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="chatbot-banner">
        <h1>🗨️  AskHR</h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------ FIXED BANNER ------------------
st.markdown(
    """
    <div class="chatbot-banner">
        <h1>🗨️  AskHR</h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="chatbot-banner">
        <h1>
            <span style="display: inline-block; transform: rotate(0deg); margin-right: 6px;">🗨️</span>
            AskHR
        </h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------ CONFIGURATION ------------------
with open("key_password.yml", "r") as file:
    config = yaml.safe_load(file)

google_key, session = streamlit_functions_langchain.connect_key_accounts(config)

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = google_key

# get vector store 
vector_store =streamlit_functions_langchain.retrieval_algorithm(google_key,session)
k_val = 5


model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

config = {"configurable": {"thread_id": "abc123"}}



def call_model(state: streamlit_functions_langchain.State):
    prompt = streamlit_functions_langchain.prompt_template.invoke(
        {'messages': state['messages'],"context":state['context'], "chat_history":state['chat_history']}
    )
    response = model.invoke(prompt)
    return {"messages": [response]}


workflow = StateGraph(streamlit_functions_langchain.State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
app = workflow.compile()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help?", "result": False}
    ]


# ------------------ QUICK HELP BUTTONS ------------------
st.markdown("### 🔍 Quick Help")
cols = st.columns(3)

if cols[0].button("📅 Leave Policy"):
    st.session_state.messages.append({"role": "user", "content": "What is the leave policy?"})
    context= vector_store.similarity_search("What is the leave policy?",k= k_val)
    retrived_chats = streamlit_functions_langchain.chat_retrieval("What is the leave policy?",session)
    chatbot_response = app.invoke({"messages":[HumanMessage("what is the leave policy of the company?")],"context":context,"chat_history":retrived_chats},config)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response['messages'][-1].content, "result": True})

if cols[1].button("⏱️ Timekeeping Rules"):
    st.session_state.messages.append({"role": "user", "content": "What are the company's timekeeping rules?"})
    context= vector_store.similarity_search("What are the company's timekeeping rules?",k= k_val)
    retrived_chats = streamlit_functions_langchain.chat_retrieval("What are the company's timekeeping rules?",session)
    chatbot_response = app.invoke({"messages":[HumanMessage("What are the company's timekeeping rules?")],"context":context,"chat_history":retrived_chats},config)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response['messages'][-1].content, "result": True})

if cols[2].button("🧾 Timesheet Submission"):
    st.session_state.messages.append({"role": "user", "content": "How do I submit my timesheet and what is the deadline?"})
    context= vector_store.similarity_search("How do I submit my timesheet and what is the deadline?",k= k_val)
    retrived_chats = streamlit_functions_langchain.chat_retrieval("How do I submit my timesheet and what is the deadline?",session)
    chatbot_response = app.invoke({"messages":[HumanMessage("How do I submit my timesheet and what is the deadline?")],"context":context,"chat_history":retrived_chats},config)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response['messages'][-1].content, "result": True})

# ------------------ CHAT INPUT ------------------
prompt_count = -1
prompt = st.chat_input()

if prompt:
    input_messages = [HumanMessage(prompt)]
    st.session_state.messages.append({"role": "user", "content": prompt})
    context= vector_store.similarity_search(prompt,k= k_val)
    retrived_chats = streamlit_functions_langchain.chat_retrieval(prompt,session)
    chatbot_response = app.invoke({"messages":input_messages,"context":context,"chat_history":retrived_chats},config)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response['messages'][-1].content, "result": True})

# ------------------ CHAT DISPLAY ------------------
for msg in st.session_state.messages:
    if msg.get("role") == "system":
        continue

    if msg.get("role") == "user":
        st.chat_message("user", avatar="👨").write(msg["content"])
        user_message = msg["content"]
    else:
        with st.chat_message("assistant", avatar="🤖"):
            prompt_count += 1
            bot_message = msg["content"]
            st.write(bot_message)

            if msg.get("result"):
                # Save to PERM table
                perm_query = (
                    "INSERT INTO CHATBOT_HISTORY_PERM(USER_RESPONSE, CHATBOT_RESPONSE) "
                    f"VALUES('{user_message.replace("'", "''")}', '{bot_message.replace("'", "''")}')"
                )
                session.sql(perm_query).collect()
