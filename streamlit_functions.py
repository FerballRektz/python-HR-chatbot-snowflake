from snowflake.connector import connect
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
import pandas as pd 
import snowflake.snowpark as sp
# gobal variables
template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use maximum sentences and explain the answer as thoroughly as possible and make it bullet form.
Always say "thanks for asking!" at the end of the answer.

{context}

Question: {question}

Helpful Answer:"""

# creating a function for .py for connecting and giving information on api key and snowflake
def connect_key_accounts(key_info: dict
                         ) -> tuple[str, object]:
    conn = connect(
    user=key_info['snowflake']['user'],  # Correct access
    password=key_info['snowflake']['password'],  # Correct access
    account=key_info['snowflake']['account'],  # Correct access
    warehouse=key_info['snowflake']['warehouse'],  # Correct access
    database=key_info['snowflake']['database'],  # Correct access
    schema=key_info['snowflake']['schema']  # Correct access
    )
    google_api_key = key_info["google"]["api-key"]

    return google_api_key,conn


# creating a function to use google api key to create llm and 
def chatbot_llm_model(google_key :str,snowflake_conn :object) -> tuple[object,object]:
    cursor = snowflake_conn.cursor()
    cursor.execute("""
    SELECT * FROM PDF_RESULTS;
    """)
    pages = []
    for row in cursor.fetchall():
        file_format = "{filename: " + row[0][:-4] +", " + row[1][6:-1]
        pages.append(file_format)

    llm = GoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=google_key)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_key)
    vector_store = InMemoryVectorStore.from_texts(pages, embeddings)



    return llm,vector_store
    

def chatbot_response(question :str, template :str, 
                     lmm_model: object, vector_store :object,k_val:int = 5) -> str:
    custom_rag_prompt = PromptTemplate.from_template(template)
    retrieved_docs = vector_store.similarity_search(question,k= k_val)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    prompt = custom_rag_prompt.invoke({"question": question, "context": docs_content})
    answer = lmm_model.invoke(prompt)
    return answer
    


# creatig a table for backend
def create_table(key_info:object) -> pd.DataFrame:
    connection_parameters = {
        "account":  key_info['snowflake']['account'],
        "user": key_info['snowflake']['user'],
        "password": key_info['snowflake']['password']
    }
    session = sp.Session.builder.configs(connection_parameters).create()
    pd_df = session.table("TRAINING_DATABASE.PUBLIC.PDF_RESULTS").limit(10)
    df = pd_df.to_pandas()
    return df

    


