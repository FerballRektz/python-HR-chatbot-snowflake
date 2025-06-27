from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import pandas as pd 
import snowflake.snowpark as sp
# gobal variables
template =  """
Context Used: {context}
Use the following context snippets and chat history to answer the user’s question accurately. Your responses must strictly follow these rules:

BEFORE ANSWERING:
1. If the question is vague  and not in the Chat History (e.g., “What is the rule?”, “What was said about it on the last page?”), respond:
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
def retrieval_algorithm(google_key :str,session:object,question:str,k_val :int = 3) -> tuple[object]:
    # Load the table to pandas

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_key)    
    pd_df = session.table("HR_CHATBOT_BACKEND.PUBLIC.PDF_RESULTS").to_pandas()
    pages = [f"[FILE: {row}]\n{pd_df["PARSED_PDF"][index]}" for index, row in enumerate(pd_df["FILEPATH"])]
    vector_store = InMemoryVectorStore.from_texts(pages, embeddings)
    retrieved_docs = vector_store.similarity_search(question,k= k_val)

    return retrieved_docs

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



    

