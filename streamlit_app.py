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
    st.session_state.messages = [{"role": "assistant", "content": "How can I help?", "result": False}]

# connect to account and get key
google_key,session = streamlit_functions.connect_key_accounts(config)




# activate llm using google key and create llm model and vector_store
lmm, vector_store = streamlit_functions.chatbot_llm_model(google_key,session)

# create_tables
df_none, df_hist = streamlit_functions.create_table(config)
streamlit_functions.create_history_table(config)

# review count
prompt_count :int = -1
review :bool = False

prompt = st.chat_input()


if prompt:
    st.session_state.messages.append({"role": "user","content": prompt})
    prompt_response = streamlit_functions.chatbot_response(prompt,streamlit_functions.template,df_hist,lmm,vector_store,K_VAL)
    st.session_state.messages.append({"role": "assistant","content": prompt_response, "result": True})

for msg in st.session_state.messages:
    if msg.get("role") == "system":
        continue 
    if msg.get("role") == "user":
        user_message = msg.get("content")
        st.chat_message("user",avatar= "🧑").write(user_message)
    else:
        with st.chat_message("assistant"):
            prompt_count+=1 
            df_none,df_hist = streamlit_functions.create_table(config)
            chat_bot_message = msg.get("content")
            st.write(chat_bot_message)
            if msg.get("result"):
                temp_query = "INSERT INTO CHATBOT_HISTORY_TEMP(Prompt_No, USER_RESPONSE, CHATBOT_RESPONSE) VALUES(" + str(prompt_count) +",'" + user_message.replace("'", "''") + "','" + chat_bot_message.replace("'", "''") + "')"
                session.sql(temp_query).collect()
                perm_query =  "INSERT INTO CHATBOT_HISTORY_PERM(USER_RESPONSE, CHATBOT_RESPONSE) VALUES(" +"'" + user_message.replace("'", "''") + "','" + chat_bot_message.replace("'", "''") + "')"
                session.sql(perm_query).collect()
                
            



