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
PACKAGES=('typing-extensions','PyPDF2','snowflake-snowpark-python')
AS
$$
from pathlib import Path
import PyPDF2 as pypdf
from io import BytesIO 
import re
from snowflake.snowpark.files import SnowflakeFile

def parse_pdf_fields(file_path):
    with SnowflakeFile.open(file_path, 'rb') as f:
       buffer = BytesIO(f.readall())
    reader = pypdf.PdfReader(buffer) 
    merged_text_list = []
    for index in range(0,len(reader.pages)):
        page_text = reader.pages[index].extract_text()
        transformed_text = re.split(r'\n|•|\s{3,10}|\d{1} of \d{1}|^[0-9]$',page_text)
        text_cleaned = [i for i in transformed_text if i !='']
        merged_text_list.extend(text_cleaned)
            
    return merged_text_list
$$;

SELECT build_scoped_file_url('@PDF_STAGE','Implementation of Time in and Time Out System Policy.pdf');

SELECT PDF_PARSE(build_scoped_file_url('@PDF_STAGE','Implementation of Time in and Time Out System Policy.pdf'));

CREATE OR REPLACE TABLE PDF_RESULTS (FILEPATH VARCHAR, PARSED_PDF VARIANT);

CREATE TASK PDF_INGEST
WAREHOUSE = COMPUTE_WH
AFTER REFRESH_PDF_STAGE
WHEN
  SYSTEM$STREAM_HAS_DATA('PDF_STREAM')
AS
  INSERT INTO PDF_RESULTS(FILEPATH, PARSED_PDF) 
  SELECT RELATIVE_PATH, 
        PARSE_JSON(PDF_PARSE(build_scoped_file_url('@PDF_STAGE',RELATIVE_PATH))) 
  FROM PDF_STREAM 
  WHERE METADATA$ACTION = 'INSERT';

SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('REFRESH_PDF_STAGE');



SELECT *, 
FROM PDF_RESULTS;
