import streamlit as st
import yaml
import streamlit_functions
import snowflake.snowpark as sp

# Import yaml 
# Load your configuration (API keys)
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)


st.title("Initial Chatbot")
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
st.write("Policy Data Table")

# connect to account and get key
google_key,conn = streamlit_functions.connect_key_accounts(config)
st.dataframe(streamlit_functions.create_table(conn))

sp.Session.builder.config