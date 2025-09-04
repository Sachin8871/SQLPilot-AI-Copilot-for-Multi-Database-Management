from Modules import connect, fetch_database
import mysql.connector
import streamlit as st
import psycopg2


#========================================= Login Section ===============================================

def connect_for_data():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["MySQL"]["MYSQL_HOST"],
            user=st.secrets["MySQL"]["MYSQL_USER"],
            port=st.secrets["MySQL"]["MYSQL_PORT"],
            password=st.secrets["MySQL"]["MYSQL_PASSWORD"],
        )
        return connection
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")



def login(user_name: str, password: str, user_type: str):
    connection = connect_for_data()
    cursor = connection.cursor()
    cursor.execute("USE user_info")

    if user_type == "New User":
        sql = "SELECT * FROM login_info WHERE username = %s"
        cursor.execute(sql, (user_name,))
        row = cursor.fetchone()
        if row:
            st.session_state.login = False
            st.warning("User already exists", icon="🚨")
        else:
            sql = "INSERT INTO login_info (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (user_name, password))
            connection.commit()
            st.success("Account Created Successfully", icon="✅")

    elif user_type == "Existing User":
        sql = "SELECT * FROM login_info WHERE username = %s AND password = %s"
        cursor.execute(sql, (user_name, password))
        row = cursor.fetchone()
        if row:
            sql = """
                SELECT d.engine, d.database_name
                FROM login_info l 
                JOIN database_data d ON l.username = d.username
                WHERE l.username = %s
            """
            cursor.execute(sql, (user_name,))
            rows = cursor.fetchall()
            for row in rows:
                # print(row)
                engine, database = row
                if str(engine) in st.session_state.user_databases:
                    st.session_state.user_databases[str(engine)].append(database)
                else:
                    st.session_state.user_databases[str(engine)] = [database]
            st.session_state.login = True
            st.write("#### Your Existing Databases")
            st.write(st.session_state.user_databases)
        else:
            st.session_state.login = False
            st.warning("User does not exist.", icon="⚠️")


def login_ui():
    st.sidebar.subheader("User Login")

    user_type = st.sidebar.radio("User Type", ["Existing User", "New User"])

    if "user_databases" not in st.session_state:
        st.session_state.user_databases = {}

    if "login" not in st.session_state:
        st.session_state.login = False

    st.session_state.user_name = st.sidebar.text_input("User Name")
    st.session_state.password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Log In") and st.session_state.user_name and st.session_state.password:
        st.session_state.user_databases = {}
        login(st.session_state.user_name, st.session_state.password, user_type)


#============================================ Database Section =============================================

def add_database(db_engine, database):
    connection = connect_for_data()
    cursor = connection.cursor()
    cursor.execute("USE user_info")
    sql = "INSERT INTO database_data (username, engine, database_name) VALUES (%s, %s, %s)"
    cursor.execute(sql, (st.session_state.user_name, db_engine, database))
    connection.commit()


def database_handler(database_type, database, db_engine):
    if database_type == "New Database":
        if db_engine in st.session_state.user_databases and database in st.session_state.user_databases[db_engine]:
            st.warning("Database already exist.", icon="⚠️")
            
        else:
            if db_engine == "MySQL": connect.connect_to_mysql(database)
            elif db_engine == "SQLite": connect.connect_to_sqlite(database)
            elif db_engine == "SQL Server": connect.connect_to_sqlserver(database)
            elif db_engine == "PostgreSQL": connect.connect_to_postgres(database)

            add_database(db_engine, database)
            if db_engine in st.session_state.user_databases:
                st.session_state.user_databases[db_engine].append(database)
            else:
                st.session_state.user_databases[db_engine] = [database]

            if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
            elif db_engine == "SQLite": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
            elif db_engine == "SQL Server": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
            elif db_engine == "PostgreSQL": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)
            st.success("Database Created Succssfully.", icon="✅")

    else:
        if db_engine in st.session_state.user_databases and database in st.session_state.user_databases[db_engine]:
            if db_engine == "MySQL": connect.connect_to_mysql(database)
            elif db_engine == "SQLite": connect.connect_to_sqlite(database)
            elif db_engine == "SQL Server": connect.connect_to_sqlserver(database)
            elif db_engine == "PostgreSQL": connect.connect_to_postgres(database)
            
            if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
            elif db_engine == "SQLite": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
            elif db_engine == "SQL Server": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
            elif db_engine == "PostgreSQL": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)

            st.success("Database Connected Succssfully.", icon="✅")

        else:
            st.warning("Database does not exist.", icon="⚠️")


#================================================ Delete database section =====================================================


def delete_database(del_database, db_engine, method):
    username = st.session_state.user_name

    if db_engine in st.session_state.user_databases and del_database in st.session_state.user_databases[db_engine]:
        if db_engine == "SQLite":
            connection = connect_for_data()
            cursor = connection.cursor()
            cursor.execute("Use user_info")
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"
            cursor.execute(sql, (username, db_engine, del_database))
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)
            if not st.session_state.user_databases[db_engine]:
                del st.session_state.user_databases[db_engine]

            if method == "by_user":
                st.success("Database Deleted.", icon="✅")
            
        elif db_engine == "PostgreSQL":
            # Connect to default DB (postgres) to create the target database
            st.session_state.connection.close()
            connection = psycopg2.connect(
                host=st.secrets["PostgreSQL"]["POSTGRES_HOST"],
                port=st.secrets['PostgreSQL']['POSTGRES_PORT'],
                user=st.secrets['PostgreSQL']['POSTGRES_USER'],
                password=st.secrets['PostgreSQL']['POSTGRES_PASSWORD'],
                dbname=st.secrets['PostgreSQL']['POSTGRES_DB']
            )
            connection.autocommit = True

            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {del_database}")
            connection.commit()
            connection.close()

            connection = connect_for_data()
            cursor = connection.cursor()
            cursor.execute("Use user_info")
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"
            cursor.execute(sql, (username, db_engine, del_database))
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)
            if not st.session_state.user_databases[db_engine]:
                del st.session_state.user_databases[db_engine]

            if method == "by_user":
                st.success("Database Deleted.", icon="✅")

        else:
            connect.connect_to_mysql(del_database)
            connection = st.session_state.connection
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {del_database}")
            connection.commit()

            connection = connect_for_data()
            cursor = connection.cursor()
            cursor.execute("Use user_info")
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"
            cursor.execute(sql, (username, db_engine, del_database))
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)
            if not st.session_state.user_databases[db_engine]:
                del st.session_state.user_databases[db_engine]

            if method == "by_user":
                st.success("Database Deleted.", icon="✅")
    else:
        st.warning(f"This {db_engine} database does not exist.", icon="⚠️")



def delete_database_by_user():
    del_database = st.sidebar.text_input("Database Name")
    db_engine = st.session_state.db_engine
    st.session_state.delete_database_fleg = True
    if st.sidebar.button("Delete") and del_database:
        delete_database(del_database, db_engine, "by_user")
        st.session_state.delete_database_fleg = False
        
    else:
        st.warning("Enter database name", icon="⚠️")


#================================================ Delete Account section =====================================================


def delete_account():
    username = st.text_input("Enter Username")
    password = st.text_input("Enter Password")
    st.session_state.delete_account_fleg = True
    if st.sidebar.button("Delete") and username and password:
        if username == st.session_state.user_name and password == st.session_state.password:
            databases = st.session_state.user_databases.copy()
            for engine, database_list in databases.items():
                for database in database_list:
                    delete_database(database, engine, "_")

            st.session_state.user_databases = {}
            connection = connect_for_data()
            cursor = connection.cursor()
            cursor.execute(f"Use user_info")
            sql = "DELETE FROM login_info WHERE username = %s"
            cursor.execute(sql, (username,))
            connection.commit()
            del st.session_state["login"]
            st.session_state.delete_account_fleg = False
            st.success("Account deleted successfully.", icon="✅")
        else:
            st.warning("Incorrect username or password.", icon="⚠️")
    else:
        st.warning("Enter username or password")