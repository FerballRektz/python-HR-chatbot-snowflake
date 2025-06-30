from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import pandas as pd 
import snowflake.snowpark as sp
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ast
# gobal variables
template =  """
Context Used: {context}
Use the following context snippets to answer the user’s question accurately. Your responses must strictly follow these rules:

BEFORE ANSWERING:
1. If the question is vague or not in chat history: {chat_history} (e.g., “What is the rule?”, “What was said about it on the last page?”), respond:
   "Could you clarify your question?"
2. If the question refers to a year or event not in the document context (e.g., “from 2010”) or not in chat history: {chat_history}, respond:
   "Sorry, the information about that time/event is not available in the provided documents."
3. Do not compare tools, platforms, or systems unless BOTH are explicitly mentioned in the document context.
4. Only reference policies, rules, or content that clearly exist in the documents provided or is in chat history : {chat_history}. Do not make assumptions.
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

3. OUT-OF-SCOPE or UNKNOWN or not in chatbot memory:
   The information you're asking for isn't available in the current context. Please try rephrasing the question.
"""



prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            template
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# State Class 
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage],add_messages]
    context: list
    chat_history: list


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

# creating retrival_algo 
def retrieval_algorithm(google_key :str,session:object) -> tuple[object]:
    # Load the table to pandas

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_key)    
    pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.PDF_RESULTS").to_pandas()

    text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
      chunk_size=2300,
      chunk_overlap=400,
      length_function=len,
      is_separator_regex=False,
    )
    pages = [text_splitter.create_documents(ast.literal_eval(lists)) for lists in pd_df['PARSED_PDF']]
    combined_pages = [page for list in pages for page in list]
    vector_store = InMemoryVectorStore.from_documents(combined_pages, embeddings)
#    retrieved_docs = vector_store.similarity_search(question,k= k_val)

    return vector_store

def chat_retrieval(question:str, session:object)->list:
      
   pd_hist = session.table("HR_CHATBOT_BACKEND.PUBLIC.CHATBOT_HISTORY_PERM").to_pandas()
   if len(pd_hist) > 0:
      if len(pd_hist) > 50:
         pd_hist = pd_hist[:len(pd_hist)-31:-1].reset_index(drop=True) #last 10
      else:
          pd_hist = pd_hist[::-1]
      chat_responses = [f"User: {pd_hist["USER_RESPONSE"][index]} AI: {value}" for index,value in enumerate(pd_hist["CHATBOT_RESPONSE"])]  
   else:
       return []
   return chat_responses



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
    pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.PDF_RESULTS").to_pandas()
    return pd_df

# create table for chatbot history creation
def chatbot_hist_to_excel(key_info : dict) -> dict:
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
   pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.CHATBOT_HISTORY_PERM").to_pandas()
   pd_df.loc[:,"USER"] = connection_parameters["user"]
   pd_df.to_excel(f"{connection_parameters['user']}_CHAT_HISTORY.xlsx",index=False)

   return pd_df



    

