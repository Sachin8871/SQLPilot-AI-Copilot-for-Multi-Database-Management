from Modules import connect, fetch_database  # Import custom modules
import mysql.connector
import streamlit as st
import psycopg2


#========================================= Login Section ===============================================

# Function to connect MySQL to update user data
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


# Function for login or signin
def login(user_name: str, password: str, user_type: str):

    connection = connect_for_data()  # Connect to MySQL to update user data
    cursor = connection.cursor()
    cursor.execute("USE user_info")  # Database to store user's signin data

    if user_type == "New User":  # If the user is new then create account

        sql = "SELECT * FROM login_info WHERE username = %s"  # Query to fetch the data weather the user is new or existing
        cursor.execute(sql, (user_name,))  # Execte query
        row = cursor.fetchone()  # Fetch only one (Since user_name is primary key so only one can exist)

        if row:  # If row is not 'None' means user already exist
            st.session_state.login = False
            st.warning("User already exists", icon="🚨")  # Warning

        else:  # If row is 'None' means user does not exist
            sql = "INSERT INTO login_info (username, password) VALUES (%s, %s)"  # Query to add user_name and password
            cursor.execute(sql, (user_name, password))  # Execute query
            connection.commit()
            st.success("Account Created Successfully", icon="✅")

    elif user_type == "Existing User":  # If user is old/existing then login for him

        sql = "SELECT * FROM login_info WHERE username = %s AND password = %s"  # Query to fetch login details
        cursor.execute(sql, (user_name, password))  # Execute query
        row = cursor.fetchone()

        if row:  # If row is not 'None' means user exist so login

            # Query to fetch user's existing databases and their engines
            sql = """
                SELECT d.engine, d.database_name
                FROM login_info l 
                JOIN database_data d ON l.username = d.username
                WHERE l.username = %s
            """
            cursor.execute(sql, (user_name,))  # Execute query
            rows = cursor.fetchall()  # Fetch all the databases

            # Store all the databases with their engines in session so that we can use them in future
            for row in rows:
                engine, database = row
                if str(engine) in st.session_state.user_databases:
                    st.session_state.user_databases[str(engine)].append(database)  # If Engine exist then append the database in user_databases
                else:
                    st.session_state.user_databases[str(engine)] = [database]  # If Engine does not exist then add both engine and database

            st.session_state.login = True  # Loging successfull
            st.write("#### Your Existing Databases")
            st.write(st.session_state.user_databases)  # Show all the databases to the user

        else:   # If row is 'None' means user does not exist
            st.session_state.login = False
            st.warning("User does not exist.", icon="⚠️")  # Warning


# Function for UI to login
def login_ui():
    st.sidebar.subheader("User Login")
    user_type = st.sidebar.radio("User Type", ["Existing User", "New User"], horizontal=True, help="Create 'New User' and login it as 'Existing User'.")  # Options for User type

    if "user_databases" not in st.session_state:
        st.session_state.user_databases = {}  # Create an empty dict to store user's existing databases

    if "login" not in st.session_state:
        st.session_state.login = False

    # Input from user for login or signin
    st.session_state.user_name = st.sidebar.text_input("User Name", help="Use temporary username.")
    st.session_state.password = st.sidebar.text_input("Password", type="password", help="Use temporary password.")

    if st.sidebar.button("Log In") and st.session_state.user_name and st.session_state.password:
        st.session_state.user_databases = {}  # Reinitialize dict if new user login with the same devise
        login(st.session_state.user_name, st.session_state.password, user_type)


#============================================ Database Section =============================================

# Function to add the database
def add_database(db_engine, database):

    connection = connect_for_data()  # Connect to MySQL for adding database
    cursor = connection.cursor()
    cursor.execute("USE user_info")  # Database to store 
    sql = "INSERT INTO database_data (username, engine, database_name) VALUES (%s, %s, %s)"  # Query to add new database for a user
    cursor.execute(sql, (st.session_state.user_name, db_engine, database))  # Execute the query
    connection.commit()


# Function to handle database connection
def database_handler(database_type, database, db_engine):
    if database_type == "New Database":  # If New then create new database
        # Check weather the database exist or not
        if db_engine in st.session_state.user_databases and database in st.session_state.user_databases[db_engine]:
            st.warning("Database already exist.", icon="⚠️")  # Database Exist
            
        else:  # Database does not exist, so create new one
            # Connect to the engine and create new database
            if db_engine == "MySQL": connect.connect_to_mysql(database)
            elif db_engine == "SQLite": connect.connect_to_sqlite(database)
            elif db_engine == "SQL Server": connect.connect_to_sqlserver(database)
            elif db_engine == "PostgreSQL": connect.connect_to_postgres(database)

            add_database(db_engine, database)  # Add this new database to admin's database for the user

            # Update user_databases in session
            if db_engine in st.session_state.user_databases:  # If engine already exist
                st.session_state.user_databases[db_engine].append(database)  # Append database
            else:  # engine does not exist
                st.session_state.user_databases[db_engine] = [database]  # Add both engine and database

            # Update database_info_str
            if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
            elif db_engine == "SQLite": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
            elif db_engine == "SQL Server": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
            elif db_engine == "PostgreSQL": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)
            st.success("Database Created Succssfully.", icon="✅")

    else:  # If already exist then connect it
        # Check weather the database exist or not
        if db_engine in st.session_state.user_databases and database in st.session_state.user_databases[db_engine]:  # database exist
            # Connect to the existing database
            if db_engine == "MySQL": connect.connect_to_mysql(database)
            elif db_engine == "SQLite": connect.connect_to_sqlite(database)
            elif db_engine == "SQL Server": connect.connect_to_sqlserver(database)
            elif db_engine == "PostgreSQL": connect.connect_to_postgres(database)
            
            # Update database_info_str
            if db_engine == "MySQL": st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
            elif db_engine == "SQLite": st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
            elif db_engine == "SQL Server": st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
            elif db_engine == "PostgreSQL": st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)

            st.success("Database Connected Succssfully.", icon="✅")

        else:  # Database does not exist
            st.warning("Database does not exist.", icon="⚠️")


#================================================ Delete database section =====================================================

# Function to delete database
def delete_database(del_database, db_engine, method):
    username = st.session_state.user_name  # Fetch user name

    # Check weather the database exist or not
    if db_engine in st.session_state.user_databases and del_database in st.session_state.user_databases[db_engine]:  # Database exist

        if db_engine == "SQLite":  # If database is of SQLite
            connection = connect_for_data()  # Connect admin's database
            cursor = connection.cursor()
            cursor.execute("Use user_info")  # Admin's database
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"  # Query to delete database from admin's data
            cursor.execute(sql, (username, db_engine, del_database))  # Execute query
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)  # Delete from user_databases in session
            if not st.session_state.user_databases[db_engine]:  # Delete engine also if it does not have any database
                del st.session_state.user_databases[db_engine]

            if method == "by_user":  # If the call from user
                st.success("Database Deleted.", icon="✅")  # Show the success message
            
        elif db_engine == "PostgreSQL":  # If database is of PostgreSQL
            # Connect to default DB because we con't delete current database in PostgreSQL
            st.session_state.connection.close()  # Close previously connected connection

            connection = psycopg2.connect(  # Connect to default database
                host=st.secrets["PostgreSQL"]["POSTGRES_HOST"],
                port=st.secrets['PostgreSQL']['POSTGRES_PORT'],
                user=st.secrets['PostgreSQL']['POSTGRES_USER'],
                password=st.secrets['PostgreSQL']['POSTGRES_PASSWORD'],
                dbname=st.secrets['PostgreSQL']['POSTGRES_DB']
            )
            connection.autocommit = True

            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {del_database}")  # Drop selected database
            connection.commit()
            connection.close()

            connection = connect_for_data()  # Connect to admin's database to update
            cursor = connection.cursor()
            cursor.execute("Use user_info")  # Admin's database
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"  # Query to delete database from admin's data
            cursor.execute(sql, (username, db_engine, del_database))  # Execute query
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)  # Delete from user_databases in session
            if not st.session_state.user_databases[db_engine]:  # Delete engine also if it does not have any database
                del st.session_state.user_databases[db_engine]

            if method == "by_user":   # If the call from user
                st.success("Database Deleted.", icon="✅")  # Show the success message

        else:  # If database is of MySQL
            connect.connect_to_mysql(del_database)  # Connect to MySQL
            connection = st.session_state.connection
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {del_database}")  # Drop the selected database
            connection.commit()

            connection = connect_for_data()  # Connect to admin's database to update
            cursor = connection.cursor()
            cursor.execute("Use user_info")  # Admin's database
            sql = "DELETE FROM database_data where username = %s and engine = %s and database_name = %s"  # Query to delete database from admin's data
            cursor.execute(sql, (username, db_engine, del_database))  # Execute query
            connection.commit()

            st.session_state.user_databases[db_engine].remove(del_database)    # Delete from user_databases in session
            if not st.session_state.user_databases[db_engine]:  # Delete engine also if it does not have any database
                del st.session_state.user_databases[db_engine]

            if method == "by_user":   # If the call from user
                st.success("Database Deleted.", icon="✅")  # Show the success message

    else:  # Database does not exist
        st.warning(f"This {db_engine} database does not exist.", icon="⚠️")


# Function to delete database for user call
def delete_database_by_user():

    del_database = st.sidebar.text_input("Database Name")  # Database name input
    db_engine = st.session_state.db_engine  # Currect database engine
    st.session_state.delete_database_fleg = True
    if st.sidebar.button("Delete") and del_database:
        delete_database(del_database, db_engine, "by_user")  # User call to dalate database
        st.session_state.delete_database_fleg = False
        
    else:
        st.warning("Enter database name", icon="⚠️")


#================================================ Delete Account section =====================================================

# Function to delete user account
def delete_account():
    # User input
    username = st.text_input("Enter Username") 
    password = st.text_input("Enter Password")

    st.session_state.delete_account_fleg = True
    if st.sidebar.button("Delete") and username and password:
        # Check username and password weather they are correct or not
        if username == st.session_state.user_name and password == st.session_state.password:  # Both are correct
           
            # === Delete all the databases of that user ===
            databases = st.session_state.user_databases.copy()  # Copy all the databases
            for engine, database_list in databases.items():  # For loop to delete
                for database in database_list:
                    delete_database(database, engine, "_")  # Delete database call by account delete

            st.session_state.user_databases = {}  # Clear user_databases in session

            connection = connect_for_data()  # Connect to admin's database to delete user
            cursor = connection.cursor()
            cursor.execute(f"Use user_info")
            sql = "DELETE FROM login_info WHERE username = %s"  # Query to deleet user
            cursor.execute(sql, (username,))  # Execute query
            connection.commit()

            del st.session_state["login"]  # Log out after deleting user account
            st.session_state.delete_account_fleg = False
            st.success("Account deleted successfully.", icon="✅")  # Success message

        else:  # Username or password is/are wrong
            st.warning("Incorrect username or password.", icon="⚠️")

    else:  # Button click with entering username or password
        st.warning("Enter username or password")


#============================================== END ===================================================
