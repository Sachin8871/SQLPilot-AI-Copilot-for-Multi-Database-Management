from Modules import sign_in, table_via_csv, fetch_database, query_execution, model_selection
from langchain_core.prompts import ChatPromptTemplate
from graph import graph
import streamlit as st


# Title of the project
st.set_page_config("SQL Agent", page_icon="🦜")
st.title("SQL Agent")

if "message_history" not in st.session_state:
    st.session_state.message_history = []

for message in st.session_state["message_history"]:
    if "user" in message:
        with st.chat_message("user"):
            st.text(message["user"])
    if "query" in message:
        with st.chat_message("assistant", avatar="📝"):
            st.code(message['query'], language='sql')
    if "result" in message:
        with st.chat_message("assistant", avatar="📊"):
            st.dataframe(message['result'])
    if "content" in message:
        with st.chat_message("ai"):
            st.text(message['content'])
    if "error" in message:
        with st.chat_message("assistant", avatar="⚠️"):
            st.error(message['error'])


if "login" not in st.session_state:
    st.warning("⚠️ Do not use your personal credentials for the username or password. This project is deployed only for testing purposes. Please use temporary login details instead.")

sign_in.login_ui()
user_input = st.chat_input("Ask anything about your database...")


if "execution_fleg" not in st.session_state:
    st.session_state.execution_fleg = False
if "error_explanation_fleg" not in st.session_state:
    st.session_state.error_explanation_fleg = False
if "delete_account_fleg" not in st.session_state:
    st.session_state.delete_account_fleg = False
if "delete_database_fleg" not in st.session_state:
    st.session_state.delete_database_fleg = False


if "login" in st.session_state and st.session_state.login:
    st.sidebar.write("Choose Database")
    database_type = st.sidebar.radio("", options=["Existing Database", "New Database"])
    database = st.sidebar.text_input("Enter database name")
    st.session_state.database = database

    db_engine = st.sidebar.selectbox("🔌 Choose a Database engine",
    options=["MySQL","SQLite","PostgreSQL"],
    index=0,
    help="""Select the database engine you want to connect to\n
        • MySQL & PostgreSQL are great for production.\n
        • SQLite is simple & file-based.\n
        • SQL Server is enterprise-grade."""
    )

    st.session_state.db_engine = db_engine
            
    if st.sidebar.button("Use") and database and db_engine:
        sign_in.database_handler(database_type, database, db_engine)


    model = model_selection.get_model()
    st.session_state.model = model
    st.session_state.config = {"configurable": {"thread_id":st.session_state.user_name}}


    show_db_structure = st.sidebar.checkbox("📂 Show Database Structure", value = False)
    table_via_csv_button = st.sidebar.checkbox("📥 Create table from csv file", value = False)
    refresh_structure = st.sidebar.button("🔄 Refresh", help="Refresh database structure")
    if st.sidebar.button("Delete Database") or st.session_state.delete_database_fleg:
        sign_in.delete_database_by_user()
    if st.sidebar.button("Delete Account") or st.session_state.delete_account_fleg:
        sign_in.delete_account()


    if refresh_structure:
        if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
        elif db_engine == "SQLite (Local)": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
        elif db_engine == "Microsoft SQL Server (SSMS)": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
        elif db_engine == "PostgreSQL-pgAdmin": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)

    if show_db_structure and "database_info_str" in st.session_state:
        st.text_area("Database Structure", st.session_state.database_info_str, height=300, disabled=True)

    if table_via_csv_button:
        st.session_state.table_via_csv = True
        table_via_csv.table_via_csv(db_engine)

    if user_input or st.session_state.execution_fleg or st.session_state.error_explanation_fleg:
        try:
            st.session_state.error_explanation_fleg = True
            if not st.session_state.execution_fleg:
                st.session_state.message_history.append({"user":user_input})
                with st.chat_message('user'):
                    st.text(user_input)
            
            if not st.session_state.execution_fleg:
                state = graph(user_input)
                st.session_state.state = state

            if st.session_state.state['task'] == "Normal_question":
                st.session_state.message_history[-1]["content"] = st.session_state.state['normal_input_ans']
                st.text(st.session_state.state["normal_input_ans"])
            else:
                query_execution.query_execute(st.session_state.state)

        except Exception as e:
            st.error(f"❌ ERROR :\n{e}")
            st.session_state.message_history[-1]["error"] = e

            if st.button("Explain Error Using AI"):
                st.session_state.error_explanation_fleg = False
                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     f"You are a helpful assistant. The database contains: \n{st.session_state.database_info_str}\n"
                     "Given the following SQL error, explain the error and give suggestions."
                     "Exapain in max 150 words"       
                    ),
                    ("human", "{error_message}")
                ])
                chain = prompt | model
                error_explanation = chain.invoke({"error_message": str(e)}).content
                st.warning(error_explanation)