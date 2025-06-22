import streamlit as st
import yaml
import streamlit_functions


# Import yaml 
# Load your configuration (API keys)
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)

K_VAL = 10

st.title("🏥 ASKHR")


if "messages" not in st.session_state:
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
    st.session_state.messages = [{"role": "assistant", "content": "How can I help?", "feedback": False}]

# connect to account and get key
google_key,session = streamlit_functions.connect_key_accounts(config)

# activate llm using google key and create llm model and vector_store
lmm, vector_store = streamlit_functions.chatbot_llm_model(google_key,session)

# create_table 
streamlit_functions.create_history_table(config)

# review count
prompt_count :int = 0


prompt = st.chat_input()
# prompt guards 


if prompt:
    st.session_state.messages.append({"role": "user","content": prompt,"result": True})
    prompt_response = streamlit_functions.chatbot_response(prompt,streamlit_functions.template,lmm,vector_store,K_VAL)
    st.session_state.messages.append({"role": "assistant","content": prompt_response,"feedback": True,"result": True})
    prompt_count+=1
    

for msg in st.session_state.messages:
    if msg.get("role") == "system":
        continue 
    if msg.get("role") == "user":
        st.chat_message("user",avatar= "🧑").write(msg.get("content"))
        if "result" in msg:
            session.sql("")
    else:
        with st.chat_message("assistant"):
            st.write(msg.get("content"))
            if msg.get("feedback"):
                nstars = st.feedback("stars",key= f"R_{prompt_count}")
                if nstars is not None:
                    st.success(f"You selected {nstars+1} star(s). Thanks for rating!", icon="😀")
            if "result" in msg:
                st.success(f"inputed in the database")

