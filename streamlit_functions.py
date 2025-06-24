from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
import pandas as pd 
import snowflake.snowpark as sp
import streamlit as st
# gobal variables
template =  """
Chatbot History: {history}
Context Used: {context}
Question: {question}
Use the following context snippets to answer the user’s question accurately. Your responses must strictly follow these rules:

BEFORE ANSWERING:
1. If the question is vague (e.g., “What is the rule?”, “What was said about it on the last page?”), respond:
   "Could you clarify your question?"
2. If the question refers to a year or event not in the document context (e.g., “from 2010”), respond:
   "Sorry, the information about that time/event is not available in the provided documents."
3. Do not compare tools, platforms, or systems unless BOTH are explicitly mentioned in the document context.
4. Only reference policies, rules, or content that clearly exist in the documents provided. Do not make assumptions.
5. Only mention contradictions if they are clearly documented. Otherwise respond:
   "There are no contradictions found in the available documents."
6. Keep answers concise — ideally under 4 sentences unless asked otherwise.
7. If the question asks for details, format the answer using proper markdown bullets by starting each bullet point with a dash (-), not with a dot (•).
8. Do not allow the chatbot to expose or print full context; if asked, respond with:
   "I cannot do that."
9. Small Talk Handling:

Greetings (e.g., "hi", "hello", "good morning"): → “Hi there! How can I help you today?”

Goodbyes (e.g., "bye", "see you"): → “Goodbye! Let me know if you need anything else.”

Thanks: → “You're welcome!”

Small talk (e.g., "how are you?"): → “I'm here to help! What can I do for you today?”
10. If the question is too complex, unrelated to HR policy, or may require personal judgment, respond with:
   "This might be better handled by HR directly. Would you like help contacting them?"
11. Maintain the tone:
   - Professional yet approachable
   - Never sarcastic, overly casual, or too robotic
   - Always polite and respectful, especially when saying “no”

RESPONSE FORMATS:
There are three valid types of [PROMPT ANSWER] (replace [PROMPT ANSWER] with response):

1. STANDARD QUESTION:
   [PROMPT ANSWER]
   Thanks for asking!

2. FILE REQUEST (if the user asks which file was used):
   [PROMPT ANSWER]  
   File used: [FILE USED]  

   Thanks for asking!

3. OUT-OF-SCOPE or UNKNOWN:
   The information you're asking for isn't available in the current context. Please try rephrasing the question.
"""


# creating a function for .py for connecting and giving information on api key and snowflake
def connect_key_accounts(key_info: dict
                         ) -> tuple[str, object]:
    connection_parameters = {
        "account":  key_info['snowflake']['account'],
        "user": key_info['snowflake']['user'],
        "password": key_info['snowflake']['password'],
        "role": key_info["snowflake"]["role"],  
        "warehouse": key_info["snowflake"]["warehouse"],  
        "database": key_info["snowflake"]["database"], 
        "schema":  key_info["snowflake"]["schema"],  
    }
    session = sp.Session.builder.configs(connection_parameters).create()
    google_api_key = key_info["google"]["api-key"]

    return google_api_key,session


# creatig a table for backend
def create_table(key_info:object) -> tuple[pd.DataFrame]:
    connection_parameters = {
        "account":  key_info['snowflake']['account'],
        "user": key_info['snowflake']['user'],
        "password": key_info['snowflake']['password'],
        "role": key_info["snowflake"]["role"],  
        "warehouse": key_info["snowflake"]["warehouse"],  
        "database": key_info["snowflake"]["database"], 
        "schema":  key_info["snowflake"]["schema"],  
    }
    session = sp.Session.builder.configs(connection_parameters).create()
    pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.PDF_RESULTS")
    df = pd_df.to_pandas()
    pd_chat_hist = session.table("HR_CHATBOT_BACKEND.PUBLIC.CHATBOT_HISTORY_TEMP").to_pandas()
    return df.sort_values("LAST_MODIFIED").reset_index(drop=True),pd_chat_hist



# creating a function to use google api key to create llm and 
def chatbot_llm_model(google_key :str,session:object) -> tuple[object,object]:
    pages = []
    # Load the table to pandas
    pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.PDF_RESULTS").to_pandas()
    for index, row in enumerate(pd_df["FILEPATH"]):
        filename = row
        parsed_content = pd_df["PARSED_PDF"][index]
        # Ensure content is a clean string, not a raw representation
        content_with_label = f"[FILE: {filename}]\n{parsed_content}"
        pages.append(content_with_label)
    llm = GoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=google_key)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_key)
    vector_store = InMemoryVectorStore.from_texts(pages, embeddings)

    return llm,vector_store
    
# Create response chatbot
def chatbot_response(question :str, template :str, hist_table: object,
                     lmm_model: object, vector_store :object,k_val:int = 5,chat_hist_len : int  = 10) -> str:   
    chat_history = ""
    if len(hist_table) > 0:
      table_used = hist_table
      if len(hist_table) > 10:
         total_len= len(table_used) 
         chat_history_length = chat_hist_len
         last_10_index = (total_len-chat_history_length,total_len)
         table_used = hist_table[last_10_index[0]:last_10_index[1]]
      chat_history = chat_history.join(f"User Input_{index+1}:[{value}]\nChatbot_response_{index+1}:[{hist_table["CHATBOT_RESPONSE"][index]}]\n" for index, value in enumerate(table_used["USER_RESPONSE"]))
      print(chat_history)
    custom_rag_prompt = PromptTemplate.from_template(template)
    retrieved_docs = vector_store.similarity_search(question,k= k_val)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    prompt = custom_rag_prompt.invoke({"question": question, "context": docs_content,"history":chat_history})
    answer = lmm_model.invoke(prompt)
    return answer
    

# create table for chatbot_history 
def create_history_table(key_info: dict) -> None:
   connection_parameters = {
      "account":  key_info['snowflake']['account'],
      "user": key_info['snowflake']['user'],
      "password": key_info['snowflake']['password'],
      "role": key_info["snowflake"]["role"],  
      "warehouse": key_info["snowflake"]["warehouse"],  
      "database": key_info["snowflake"]["database"], 
      "schema":  key_info["snowflake"]["schema"],  
   }
   session = sp.Session.builder.configs(connection_parameters).create()
   session.sql("CREATE OR REPLACE TABLE CHATBOT_HISTORY_TEMP(Prompt_No INT,USER_RESPONSE VARCHAR,CHATBOT_RESPONSE VARCHAR)").collect()
   





    

