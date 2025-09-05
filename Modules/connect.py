from psycopg2 import sql
import streamlit as st
import mysql.connector
import psycopg2
import sqlite3
import pyodbc


#========================================= Connect to MySQL =============================================

def connect_to_mysql(database):
    try:
        connection = mysql.connector.connect(
            host=st.secrets["MySQL"]["MYSQL_HOST"],
            user=st.secrets["MySQL"]["MYSQL_USER"],
            port=st.secrets["MySQL"]["MYSQL_PORT"],
            password=st.secrets["MySQL"]["MYSQL_PASSWORD"],
        )
        cursor = connection.cursor()
        
        try:  # Firstly try to create the database if it is not exist
            cursor.execute(f"CREATE DATABASE {database}")
            connection.commit()

        except:  # otherwise use it if it exist
            cursor.execute(f"Use {database}")
            connection.commit()

        st.session_state.connection = connection
    except mysql.connector.Error as e:
        st.error(f"❌ Connection failed: {e}")


#=========================================== Connect to SQLite ==================================================

def connect_to_sqlite(database):
    try:  # This handles both cases existing or non existing databases (If it exist, connect that otherwise create new one)
        connection = sqlite3.connect(database, check_same_thread=False)
        st.session_state.connection = connection
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")


#=========================================== Connect to PostgreSQL ==================================================

def connect_to_postgres(database: str):
    try:
        # Try connecting directly to the target database
        connection = psycopg2.connect(
            host=st.secrets["PostgreSQL"]["POSTGRES_HOST"],
            port=st.secrets['PostgreSQL']['POSTGRES_PORT'],
            user=st.secrets['PostgreSQL']['POSTGRES_USER'],
            password=st.secrets['PostgreSQL']['POSTGRES_PASSWORD'],
            dbname=database
        )
        connection.autocommit = True
        st.session_state.connection = connection

    except Exception:
        try:
            # Connect to default DB (postgres) to create the target database
            fallback_conn = psycopg2.connect(
                host=st.secrets["PostgreSQL"]["POSTGRES_HOST"],
                port=st.secrets['PostgreSQL']['POSTGRES_PORT'],
                user=st.secrets['PostgreSQL']['POSTGRES_USER'],
                password=st.secrets['PostgreSQL']['POSTGRES_PASSWORD'],
                dbname=st.secrets['PostgreSQL']['POSTGRES_DB']
            )
            fallback_conn.autocommit = True
            cursor = fallback_conn.cursor()

            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database))
            )

            cursor.close()
            fallback_conn.close()

            # Reconnect to the newly created database
            connection = psycopg2.connect(
                host=st.secrets["PostgreSQL"]["POSTGRES_HOST"],
                port=st.secrets['PostgreSQL']['POSTGRES_PORT'],
                user=st.secrets['PostgreSQL']['POSTGRES_USER'],
                password=st.secrets['PostgreSQL']['POSTGRES_PASSWORD'],
                dbname=database
            )
            connection.autocommit = True
            st.session_state.connection = connection

        except Exception as e:
            st.error(f"❌ Failed to create/connect database: {e}")


#=========================================== Connect to SQL server ==================================================

def connect_to_sqlserver(database: str):
    try:
        # Step 1: Try connecting directly to the target database
        connection = pyodbc.connect(
            f"DRIVER={st.secrets['PostgreSQL']['SQLSERVER_DRIVERT']};"
            f"SERVER={st.secrets['PostgreSQL']['SQLSERVER_SERVER']};"
            f"DATABASE={database};"
            f"UID={st.secrets['PostgreSQL']['SQLSERVER_UID']};"
            f"PWD={st.secrets['PostgreSQL']['SQLSERVER_PWD']};"
            "Trusted_Connection=no;",
            autocommit=True
        )
        st.session_state.connection = connection
        return connection

    except Exception:
        try:
            # Step 2: Connect to fallback (master) to create the target database
            fallback_conn = pyodbc.connect(
                f"DRIVER={st.secrets['PostgreSQL']['SQLSERVER_DRIVERT']};"
                f"SERVER={st.secrets['PostgreSQL']['SQLSERVER_SERVER']};"
                "DATABASE=master;"
                f"UID={st.secrets['PostgreSQL']['SQLSERVER_UID']};"
                f"PWD={st.secrets['PostgreSQL']['SQLSERVER_PWD']};"
                "Trusted_Connection=no;",
                autocommit=True
            )
            cursor = fallback_conn.cursor()

            # Safe database creation (quotes prevent weird names from breaking SQL)
            cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{database}') CREATE DATABASE [{database}]")
            
            cursor.close()
            fallback_conn.close()

            # Step 3: Reconnect to the newly created database
            connection = pyodbc.connect(
                f"DRIVER={st.secrets['PostgreSQL']['SQLSERVER_DRIVERT']};"
                f"SERVER={st.secrets['PostgreSQL']['SQLSERVER_SERVER']};"
                f"DATABASE={database};"
                f"UID={st.secrets['PostgreSQL']['SQLSERVER_UID']};"
                f"PWD={st.secrets['PostgreSQL']['SQLSERVER_PWD']};"
                "Trusted_Connection=no;",
                autocommit=True
            )
            st.session_state.connection = connection

        except Exception as e:
            st.error(f"❌ Failed to create/connect database: {e}")


#=================================================== END ==========================================================
