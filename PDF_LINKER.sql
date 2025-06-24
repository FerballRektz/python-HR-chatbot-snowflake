CREATE OR REPLACE STAGE PDF_STAGE DIRECTORY = (ENABLE = TRUE);

CREATE OR REPLACE TASK REFRESH_PDF_STAGE
SCHEDULE = '1 MINUTE'
AS
ALTER STAGE PDF_STAGE REFRESH;

ALTER TASK REFRESH_PDF_STAGE RESUME;

CREATE OR REPLACE STREAM PDF_STREAM ON DIRECTORY(@PDF_STAGE);

SELECT * FROM PDF_STREAM;


CREATE OR REPLACE FUNCTION PDF_PARSE(file_path string)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
HANDLER = 'parse_pdf_fields'
PACKAGES=('typing-extensions','snowflake-snowpark-python','pypdf','langchain-community')
AS
$$
from io import BytesIO 
from snowflake.snowpark.files import SnowflakeFile
from langchain_community.document_loaders import PyPDFLoader

def parse_pdf_fields(file_path):
    tmp_file_path = "/tmp/temp_file.pdf"
    with SnowflakeFile.open(file_path, 'rb') as f_in, open(tmp_file_path, "wb") as f_out:
        f_out.write(f_in.readall())

    loader = PyPDFLoader(tmp_file_path).load()

    text_list = [str(item.metadata) + "  true_page_number:" + str(page_number+1) + ", " + "page_content: " + item.page_content for page_number,item in enumerate(loader)]

    return text_list

$$;

SELECT build_scoped_file_url('@PDF_STAGE','LPI TIMESHEET SUBMISSION POLICY.pdf')
SELECT PDF_PARSE(build_scoped_file_url('@PDF_STAGE','Implementation of Time in and Time Out System Policy.pdf'));




CREATE OR REPLACE TABLE PDF_RESULTS (FILEPATH VARCHAR, PARSED_PDF VARIANT,LAST_MODIFIED DATETIME);

CREATE OR REPLACE TABLE CHATBOT_HISTORY_PERM(USER_RESPONSE VARCHAR,CHATBOT_RESPONSE VARCHAR);

CREATE OR REPLACE TASK PDF_INGEST
WAREHOUSE = CHATBOT_TEST
AFTER REFRESH_PDF_STAGE
WHEN
  SYSTEM$STREAM_HAS_DATA('PDF_STREAM')
AS
  INSERT INTO PDF_RESULTS(FILEPATH, PARSED_PDF,LAST_MODIFIED) 
  SELECT RELATIVE_PATH, 
        PARSE_JSON(PDF_PARSE(build_scoped_file_url('@PDF_STAGE',RELATIVE_PATH))),
        CURRENT_TIMESTAMP(2)
  FROM PDF_STREAM 
  WHERE METADATA$ACTION = 'INSERT';


SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('REFRESH_PDF_STAGE');


SELECT * 
FROM PDF_RESULTS; 

SELECT * 
FROM CHATBOT_HISTORY_PERM;


SELECT * 
FROM CHATBOT_HISTORY_TEMP;


INSERT INTO CHATBOT_HISTORY_TEMP(Prompt_No, USER_RESPONSE, CHATBOT_RESPONSE, REVIEW) VALUES(2,'hello','The information you''re asking for isn''t available in the current context. Please try rephrasing the question',5);


DELETE FROM PDF_RESULTS WHERE FILEPATH = 'Implementation of Time in and Time Out System Policy.pdf'