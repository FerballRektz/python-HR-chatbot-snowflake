import streamlit as st
import yaml
import streamlit_functions
import snowflake.snowpark as sp
import pathlib as path
# Import yaml 
# Load your configuration (API keys)
with open("keys.yml", "r") as file:
    config = yaml.safe_load(file)


st.title("📤 Policy File Uploader Snowflake")
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
st.write("Policy Data Table")

connection_parameters = {
    "account":  config['snowflake']['account'],
    "user": config['snowflake']['user'],
    "password": config['snowflake']['password'],
    "role": config["snowflake"]["role"],  # optional
    "warehouse": config["snowflake"]["warehouse"],  # optional
    "database": config["snowflake"]["database"], # optional
    "schema":  config["snowflake"]["schema"],  # optional
    
}
session = sp.Session.builder.configs(connection_parameters).create()


# check for intellection folder in directory
file_name = path.Path('Intellection')

df = streamlit_functions.create_table(config)
df_current_files = [ "Intellection\\" + str(i) for i in df['FILEPATH']]

INTELLECTION_STR_LEN = 13;

#  creating checkboxes
if not file_name.exists():
    st.error("Directory does not exist.")
else:
    pdf_file_name = [str(pdf) + " (Uploaded)" if str(pdf) in df_current_files else str(pdf) for pdf in file_name.glob("*.pdf")]
    pdf_file_items  = [str(pdf) for pdf in file_name.glob("*.pdf")]
    pdf_file_location = [str(pdf.absolute()) for pdf in file_name.glob("*.pdf")]

    if not pdf_file_name:
        st.warning("No PDF files found.")
    else:
        st.subheader("Select files to upload:")
        selected_files = []
        for file in pdf_file_name:
            if st.checkbox(file[INTELLECTION_STR_LEN:]):
                selected_files.append(pdf_file_location[pdf_file_name.index(file)])

        if st.button("Upload Selected"):
            uploaded_count = 0
            for file in selected_files:
                try:    
                    file_check = pdf_file_items[pdf_file_location.index(file)]
                    if file_check in df_current_files:
                        try:
                            session.sql("DELETE FROM PDF_RESULTS WHERE FILEPATH =" + f"'{file_check[13:]}'").collect()
                            st.success(f"✅ Deleted Duplicate File {file_check}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    session.file.put(
                        local_file_name=str(file),
                        stage_location= config['snowflake']['stage_name'],
                        overwrite=True,
                        auto_compress= False
                    )
                    st.success(f"✅ Uploaded {file}")
                    uploaded_count += 1
                except Exception as e:
                    st.error(f"❌ Failed to upload {file}: {e}")

            if uploaded_count == 0:
                st.info("No files uploaded.")




# show database
st.dataframe(df[["FILEPATH","PARSED_PDF"]])

