from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
import streamlit as st
from Modules import fetch_database
import pandas as pd
import re


def query_execute(state):
    db_engine = st.session_state.db_engine
    cursor = st.session_state.connection.cursor()
    database = st.session_state.database
    model = st.session_state.model

    query = st.session_state.state["query"]
    if not st.session_state.execution_fleg:
        st.session_state.message_history[-1]["query"] = query
        
    st.code(query, language="sql")

    if st.session_state.state["type"] == 'read':
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        st.write(f"#### Output of the query")   
        st.session_state.message_history[-1]["result"] = df
        st.dataframe(df)
        content = f"Fetched {len(rows)} rows with columns {columns}."
        st.session_state.message_history[-1]["content"] = content
        st.write(content)

    elif st.session_state.state["type"] == 'modify':
        st.session_state.execution_fleg = True

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a helpful assistant. The database contains: \n{st.session_state.database_info_str}\n"
                    "Given the following modification SQL query, explain the query as warning what changes it does in database (in max 3 lines)."),
            ("human", "{error_message}")    
        ])
        chain = prompt | model
        raw_output_2 = chain.invoke({"error_message": str(query)}).content
        query_explanation = re.sub(r"<think>.*?</think>", "", raw_output_2, flags=re.DOTALL).strip()
        st.warning(f"Warning \n\n {query_explanation} \n\n Do you still want to execute the query.", icon="🚨")

        col3, col4 = st.columns([7.5, 1])
        with col3:
            if st.button("Yes, execute"):
                st.session_state.executed = True
                st.session_state.execution_fleg = False
                del st.session_state["execution_fleg"]

        with col4:
            if st.button("Cancel"):
                st.session_state.cancelled = True
                st.session_state.execution_fleg = False
                del st.session_state["execution_fleg"]
                
    if "executed" in st.session_state:
        cursor.execute(query)
        st.session_state.connection.commit()
        st.session_state.message_history[-1]["content"] = "Query executed successfully."

        if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
        elif db_engine == "SQLite (Local)": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
        elif db_engine == "Microsoft SQL Server (SSMS)": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
        elif db_engine == "PostgreSQL-pgAdmin": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)
        
        st.text("Query executed successfully.")
        st.success(f"Successfully executed\n\n`{query}`", icon="✅")
        st.session_state.warning_fleg = True
        del st.session_state["executed"]

    if "cancelled" in st.session_state:
        st.session_state.message_history[-1]["content"] = "Query not executed as user reject it."
        st.text("Query not executed as user reject it.")
        st.success("Cancelled.", icon="✅")
        st.session_state.warning_fleg = True
        del st.session_state["cancelled"]