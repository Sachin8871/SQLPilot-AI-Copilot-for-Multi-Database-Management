from Modules import fetch_database   # Custom module to fetch updated DB info
import streamlit as st
import pandas as pd


# Function to create table in DB from uploaded CSV
def table_via_csv(db_engine):   

    database = st.session_state.database   # Get selected database from session
    st.write("#### 📥 Upload CSV to Create Table")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")   # File uploader for CSV

    if uploaded_file:
        df_csv = pd.read_csv(uploaded_file)   # Read CSV into dataframe

        st.write("### Preview of Uploaded CSV")   # Show preview text
        st.dataframe(df_csv.head())   # Display first rows of uploaded CSV

        table_name = st.text_input("Enter table name to create in database:")   # Input for table name

        if table_name and st.button("Create Table from CSV"):
            try:
                connection = st.session_state.connection   # DB connection from session
                cursor = connection.cursor()

                # === Infer SQL column types ===
                def infer_sql_type(series):   # Helper to map pandas dtype to SQL type
                    if pd.api.types.is_integer_dtype(series):
                        return "INT"
                    elif pd.api.types.is_float_dtype(series):
                        return "FLOAT"
                    elif pd.api.types.is_bool_dtype(series):
                        return "BOOLEAN"
                    else:
                        return "VARCHAR(255)"   # Default to string

                columns = df_csv.columns   # Extract column names
                dtypes = [infer_sql_type(df_csv[col]) for col in columns]   # Infer SQL types for each column

                # === Quote table and column names to avoid reserved words ===
                quoted_columns = [f'"{col}" {dtype}' for col, dtype in zip(columns, dtypes)]   # Safe column definitions
                create_stmt = f'CREATE TABLE {table_name} (\n' + ",\n".join(quoted_columns) + "\n);"   # Full CREATE TABLE statement

                cursor.execute(create_stmt)   # Execute CREATE TABLE query

                # === Prepare insert placeholders based on DB engine ===
                if db_engine in ["MySQL", "PostgreSQL"]:
                    placeholders = ', '.join(['%s'] * len(columns))
                elif db_engine in ["SQLite", "SQL Server"]:
                    placeholders = ', '.join(['?'] * len(columns))
                else:
                    raise ValueError(f"Unsupported DB engine: {db_engine}")   # Error for unknown DB

                insert_stmt = f'INSERT INTO "{table_name}" VALUES ({placeholders})'   # Insert statement

                # === Insert rows ===
                for _, row in df_csv.iterrows():   # Iterate over dataframe rows
                    row_values = [None if pd.isna(val) else val for val in row]   # Replace NaN with None
                    cursor.execute(insert_stmt, tuple(row_values))   # Insert row into DB

                connection.commit()   # Commit transaction

                # === Refresh structure in session ===
                if db_engine == "MySQL":
                    st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
                elif db_engine == "SQLite (Local)":
                    st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
                elif db_engine == "Microsoft SQL Server (SSMS)":
                    st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
                elif db_engine == "PostgreSQL-pgAdmin":
                    st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)

                st.success(f"✅ Table `{table_name}` created and {len(df_csv)} rows inserted.")   # Success message
                del st.session_state["table_via_csv"]   # Clear session key to reset function state

            except Exception as e:
                st.error("❌ Failed to create table or insert data.")
                st.exception(e)   # Print full exception details


#============================================== END ===========================================
