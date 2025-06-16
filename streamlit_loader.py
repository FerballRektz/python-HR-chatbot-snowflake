import streamlit as st
import yaml
import streamlit_functions

# Import yaml 
# Load your configuration (API keys)
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)


st.title("📤 Policy File Uploader Snowflake")
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
st.write("Policy Data Table")

# connect to account and get key
df = streamlit_functions.create_table(config)
st.dataframe(df)