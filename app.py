from Modules import sign_in, table_via_csv, fetch_database, query_execution, model_selection
from langchain_core.prompts import ChatPromptTemplate
from graph import graph
import streamlit as st


# Title of the project
st.set_page_config("SQLPilot", page_icon="🦜")
st.set_page_config(page_title="SQLPilot", page_icon="🦜")

# Centered title
st.markdown("""<h1 style='text-align: center;'>SQLPilot 🦜</h1>""",unsafe_allow_html=True)


#============================================ Session state variable =======================================================

# Define session_state variable
if "message_history" not in st.session_state:  # To store history of conversation
    st.session_state.message_history = []
if "execution_fleg" not in st.session_state:   # To implement nexted button for query execution
    st.session_state.execution_fleg = False
if "delete_account_fleg" not in st.session_state:  # To implement nexted button for account deletion
    st.session_state.delete_account_fleg = False
if "delete_database_fleg" not in st.session_state:  # # To implement nexted button for database deletion
    st.session_state.delete_database_fleg = False
if "user_input_fleg" not in st.session_state:  # To handle "None" user input
    st.session_state.user_input_fleg = False


#=============================================== Message History =========================================================

# Display message history
for message in st.session_state["message_history"]:
    
    if "user" in message: # For User input
        with st.chat_message("user"):
            st.text(message["user"])
    if "query" in message: # For generated query
        with st.chat_message("assistant", avatar="📝"):
            st.code(message['query'], language='sql')    
    if "result" in message: # For query output
        with st.chat_message("assistant", avatar="📊"):
            st.dataframe(message['result'])
    if "content" in message: # For AI output
        with st.chat_message("ai"):
            st.text(message['content'])
    if "error" in message: # For Error
        with st.chat_message("assistant", avatar="⚠️"):
            st.error(message['error'])


#=============================================== User Login =========================================================

# Warning for personal credentials
if "login" not in st.session_state:
    st.warning("⚠️ Do not use your personal credentials for the username or password. This project is deployed only for testing purposes. Please use temporary login details instead.")


sign_in.login_ui()  # User login/signin
# User input in chatbot
user_input = st.chat_input("Ask anything about your database...")
if user_input:  # Avoid implementing user input "None"
    st.session_state.user_input_fleg = True


#=============================================== Login Section =========================================================

if "login" in st.session_state and st.session_state.login:

    # Option for database type New / Existing
    st.sidebar.subheader("Database Selection")
    database_type = st.sidebar.radio("Database type", options=["Existing Database", "New Database"], horizontal=True, help="Create 'New Database', and login it as 'Existing Database'.")
    database = st.sidebar.text_input("Enter database name")
    st.session_state.database = database

    # Select database engine
    db_engine = st.sidebar.selectbox("🔌 Choose a Database engine",
    options=["MySQL","SQLite","PostgreSQL"],
    index=0,
    help="""Select the database engine you want to connect to\n
        • MySQL & PostgreSQL are great for production.\n
        • SQLite is simple & file-based."""
    )

    # Store database engine in session state to multyple use
    st.session_state.db_engine = db_engine
            
    # Connect or Create Database after database and db_engine input
    if st.sidebar.button("Use") and database and db_engine:
        sign_in.database_handler(database_type, database, db_engine)


    #============================================ LLM Model Selection ======================================================

    model = model_selection.get_model()
    st.session_state.model = model     # Store model in session state for feather use
    # Unique thread id for different different user
    st.session_state.config = {"configurable": {"thread_id":st.session_state.user_name}} 


    #============================================= Sidebar buttons =========================================================

    st.sidebar.subheader("More Options")
    # Show database structure anytime with tables, their columns and constraints
    show_db_structure = st.sidebar.checkbox("📂 Show Database Structure", value = False)
    if show_db_structure and "database_info_str" in st.session_state:
        st.text_area("Database Structure", st.session_state.database_info_str, height=300, disabled=True)

    # Create table using CSV (Helpfull for large tables)
    table_via_csv_button = st.sidebar.checkbox("📥 Create table from csv file", value = False)
    if table_via_csv_button:
        st.session_state.table_via_csv = True  # To handle Nexted button
        table_via_csv.table_via_csv(db_engine)

    # Delete database button
    if st.sidebar.button("Delete Database") or st.session_state.delete_database_fleg:
        sign_in.delete_database_by_user()

    # Delete account button
    if st.sidebar.button("Delete Account") or st.session_state.delete_account_fleg:
        sign_in.delete_account()

    # Refreash Button to refreash database_info_str
    refresh_structure = st.sidebar.button("🔄 Refresh", help="Refresh database structure")
    if refresh_structure:  # Refreash Database structure
        if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
        elif db_engine == "SQLite (Local)": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
        elif db_engine == "Microsoft SQL Server (SSMS)": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
        elif db_engine == "PostgreSQL-pgAdmin": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)


    #============================================ Implementing Graph =================================================================

    if user_input or st.session_state.execution_fleg:
        try:
            if st.session_state.user_input_fleg:
                st.session_state.message_history.append({"user":user_input})  # Store user input in message history
                with st.chat_message('user'):
                    st.text(user_input)  # Display user input in chatbot
            
            # Generate output for user input
            if st.session_state.user_input_fleg:
                state = graph(user_input)  # Implement graph execution
                st.session_state.state = state  # Store it in session state

            if st.session_state.state['task'] == "Normal_question":
                st.session_state.message_history[-1]["content"] = st.session_state.state['normal_input_ans']  # Store ai ans in message history
                with st.chat_message("ai"):
                    st.text(st.session_state.state["normal_input_ans"])  # Display ai answer
            else:
                query_execution.query_execute(st.session_state.state)  # Execute query in database for result

        # Error handling if any
        except Exception as e:
            st.error(f"❌ ERROR :\n{e}")
            st.session_state.message_history[-1]["error"] = e  # Store Error in message history


#======================================= END ==========================================================
