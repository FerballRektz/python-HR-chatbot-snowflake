import streamlit as st
import yaml
import streamlit_functions

# ------------------ PAGE CONFIG + STYLING ------------------
st.set_page_config(page_title="❓ AskHR", layout="centered")

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
        <h1>❓  AskHR</h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------ FIXED BANNER ------------------
st.markdown(
    """
    <div class="chatbot-banner">
        <h1>❓  AskHR</h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="chatbot-banner">
        <h1>
            <span style="display: inline-block; transform: rotate(50deg); margin-right: 6px;">❓</span>
            AskHR
        </h1>
        <p>Your Workplace Assistant</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------ CONFIGURATION ------------------
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help?", "result": False}
    ]

google_key, session = streamlit_functions.connect_key_accounts(config)

# ------------------ QUICK HELP BUTTONS ------------------
st.markdown("### 🔍 Quick Help")
cols = st.columns(3)

if cols[0].button("📅 Leave Policy"):
    st.session_state.messages.append({"role": "user", "content": "What is the leave policy?"})
    context,history = streamlit_functions.retrieval_algorithm(google_key,session,"what is the leave policy of the company?")
    chatbot_response = streamlit_functions.chat_response(google_key,streamlit_functions.template,context,"what is the leave policy of the company?",history)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response, "result": True})

if cols[1].button("⏱️ Timekeeping Rules"):
    st.session_state.messages.append({"role": "user", "content": "What are the company's timekeeping rules?"})
    context,history = streamlit_functions.retrieval_algorithm(google_key,session,"What are the company's timekeeping rules?")
    chatbot_response = streamlit_functions.chat_response(google_key,streamlit_functions.template,context,"What are the company's timekeeping rules?",history)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response, "result": True})

if cols[2].button("🧾 Timesheet Submission"):
    st.session_state.messages.append({"role": "user", "content": "How do I submit my timesheet and what is the deadline?"})
    context,history = streamlit_functions.retrieval_algorithm(google_key,session,"How do I submit my timesheet and what is the deadline?")
    chatbot_response = streamlit_functions.chat_response(google_key,streamlit_functions.template,context,"How do I submit my timesheet and what is the deadline?",history)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response, "result": True})

# ------------------ CHAT INPUT ------------------
prompt_count = -1
prompt = st.chat_input()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    context,history = streamlit_functions.retrieval_algorithm(google_key,session,prompt)
    chatbot_response = streamlit_functions.chat_response(google_key,streamlit_functions.template,context,prompt,history)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response, "result": True})

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
