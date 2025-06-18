import streamlit as st
import yaml
import streamlit_functions


# Import yaml 
# Load your configuration (API keys)
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)


st.title("🏥 ASKHR")


if "messages" not in st.session_state:
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
    st.session_state.messages = [{"role": "assistant", "content": "How can I help?"}]

# connect to account and get key
google_key,conn = streamlit_functions.connect_key_accounts(config)

# activate llm using google key and create llm model and vector_store
lmm, vector_store = streamlit_functions.chatbot_llm_model(google_key,conn)




prompt = st.chat_input()
# prompt guards 


if prompt:
    st.session_state.messages.append({"role": "user","content": prompt})
    prompt_response = streamlit_functions.chatbot_response(prompt,streamlit_functions.template,lmm,vector_store,5)
    st.session_state.messages.append({"role": "assistant","content": prompt_response})




for msg in st.session_state.messages:
    if msg.get("role") == "system":
        continue 
    if msg.get("role") == "user":
        st.chat_message("user",avatar= "🧑").write(msg.get("content"))
    else:
        with st.chat_message("assistant"):
            st.write(msg.get("content"))
            if "results" in msg:
                st.dataframe(msg.get("results"))