from Modules import fetch_database  # Import custom module to fetch database
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
import pandas as pd
import re


# Function for query execution
def query_execute(state):

    #========================================= Fetch variables ==========================================

    db_engine = st.session_state.db_engine  # Fetching db engine
    cursor = st.session_state.connection.cursor()  # Connection for db engine
    database = st.session_state.database  # Database in which the query will be executed
    model = st.session_state.model  # Model to write modification warning

    query = st.session_state.state["query"]   # Fetching query fom session state to execute
    if not st.session_state.execution_fleg:
        st.session_state.message_history[-1]["query"] = query  # Store query in message history
    
    with st.chat_message("assistant", avatar="📝"):
        st.code(query, language="sql")  # Show query in chatbot


    #========================================= Read query execution ==========================================

    if st.session_state.state["type"] == 'read':

        cursor.execute(query)  # Execute query in the database
        rows = cursor.fetchall()  # Fetch the data / rows

        columns = [desc[0] for desc in cursor.description]  # Columns of the data
        df = pd.DataFrame(rows, columns=columns)  # Create dataframe
        st.session_state.message_history[-1]["result"] = df  # Store df in message history

        # st.write(f"#### Output of the query")
        with st.chat_message("assistant", avatar="📊"):
            st.dataframe(df)  # Show df in chatbot

        content = f"Fetched {len(rows)} rows with columns {columns}."  # Content / final messaege
        st.session_state.message_history[-1]["content"] = content  # Store it to message history 
        with st.chat_message("ai"):
            st.write(content)  # Show the content in chatbot


    #========================================= Modify query execution ==========================================

    elif st.session_state.state["type"] == 'modify':
        st.session_state.execution_fleg = True

        # prompt to write warning for modify query
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a helpful assistant. The database contains: \n{st.session_state.database_info_str}\n"
                    "Given the following modification SQL query, explain the query as warning what changes it does in database (in max 3 lines)."),
            ("human", "{error_message}")    
        ])
        chain = prompt | model
        raw_output_2 = chain.invoke({"error_message": str(query)}).content
        query_explanation = re.sub(r"<think>.*?</think>", "", raw_output_2, flags=re.DOTALL).strip()   # Remove extra part like <think>
        st.warning(f"Warning \n\n {query_explanation} \n\n Do you still want to execute the query.", icon="🚨")  # Show warinig to the user

        # Columns for "Yes, Execute" and "cancel" buttons
        col3, col4 = st.columns([7.5, 1])
        with col3:
            if st.button("Yes, execute"):
                st.session_state.executed = True  # If yes clicked then create "executed" in session state
                st.session_state.execution_fleg = False  # So that this part will not be executed after next input
                del st.session_state["execution_fleg"]

        with col4:
            if st.button("Cancel"):
                st.session_state.cancelled = True  # If Cancel clicked then create "cancelled" in session state
                st.session_state.execution_fleg = False  # So that this part will not be executed after next input
                del st.session_state["execution_fleg"]


    #-------------------------- Execute Query --------------------------------
                
    if "executed" in st.session_state:
        cursor.execute(query)  # Execute the query if "Yes, execute" clicked
        st.session_state.connection.commit()
        st.session_state.message_history[-1]["content"] = "Query executed successfully."  # store a simple message for user
        
        # Update the database structure in session
        if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
        elif db_engine == "SQLite (Local)": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
        elif db_engine == "Microsoft SQL Server (SSMS)": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
        elif db_engine == "PostgreSQL-pgAdmin": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)
        
        with st.chat_message("ai"):
            st.text("Query executed successfully.")  # Show the message in chatbot

        st.success(f"Successfully executed\n\n`{query}`", icon="✅")
        st.session_state.warning_fleg = True
        del st.session_state["executed"]


    #-------------------------- Cancel execution ---------------------------------

    if "cancelled" in st.session_state:  # Cancel the execute the query if "Cancel" clicked
        st.session_state.message_history[-1]["content"] = "Query not executed as user reject it."  # store a simple message for user
        with st.chat_message("ai"):
            st.text("Query not executed as user reject it.")  # Show the message in chatbot

        st.success("Cancelled.", icon="✅")
        st.session_state.warning_fleg = True
        del st.session_state["cancelled"]


#=============================================== END =============================================
