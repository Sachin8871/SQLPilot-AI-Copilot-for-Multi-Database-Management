import streamlit as st
from Modules import fetch_database
import pandas as pd


def table_via_csv(db_engine):
    database = st.session_state.database
    st.write("#### 📥 Upload CSV to Create Table")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file:
        df_csv = pd.read_csv(uploaded_file)

        st.write("### Preview of Uploaded CSV")
        st.dataframe(df_csv.head())

        table_name = st.text_input("Enter table name to create in database:")

        if table_name and st.button("Create Table from CSV"):
            try:
                connection = st.session_state.connection
                cursor = connection.cursor()

                # === Infer SQL column types ===
                def infer_sql_type(series):
                    if pd.api.types.is_integer_dtype(series):
                        return "INT"
                    elif pd.api.types.is_float_dtype(series):
                        return "FLOAT"
                    elif pd.api.types.is_bool_dtype(series):
                        return "BOOLEAN"
                    else:
                        return "VARCHAR(255)"

                columns = df_csv.columns
                dtypes = [infer_sql_type(df_csv[col]) for col in columns]

                # === Quote table and column names to avoid reserved words ===
                quoted_columns = [f'"{col}" {dtype}' for col, dtype in zip(columns, dtypes)]
                create_stmt = f'CREATE TABLE {table_name} (\n' + ",\n".join(quoted_columns) + "\n);"

                cursor.execute(create_stmt)

                # === Prepare insert placeholders based on DB engine ===
                if db_engine in ["MySQL", "PostgreSQL"]:
                    placeholders = ', '.join(['%s'] * len(columns))
                elif db_engine in ["SQLite", "SQL Server"]:
                    placeholders = ', '.join(['?'] * len(columns))
                else:
                    raise ValueError(f"Unsupported DB engine: {db_engine}")

                insert_stmt = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

                # === Insert rows ===
                for _, row in df_csv.iterrows():
                    row_values = [None if pd.isna(val) else val for val in row]
                    cursor.execute(insert_stmt, tuple(row_values))

                connection.commit()

                # === Refresh structure in session ===
                if db_engine == "MySQL":
                    st.session_state.database_info_str = fetch_database.fetch_db_mysql(st.session_state.connection, database)
                elif db_engine == "SQLite (Local)":
                    st.session_state.database_info_str = fetch_database.fetch_db_sqlite(st.session_state.connection, database)
                elif db_engine == "Microsoft SQL Server (SSMS)":
                    st.session_state.database_info_str = fetch_database.fetch_db_sqlserver(st.session_state.connection, database)
                elif db_engine == "PostgreSQL-pgAdmin":
                    st.session_state.database_info_str = fetch_database.fetch_db_postgresql(st.session_state.connection, database)

                st.success(f"✅ Table `{table_name}` created and {len(df_csv)} rows inserted.")
                del st.session_state["table_via_csv"]

            except Exception as e:
                st.error("❌ Failed to create table or insert data.")
                st.exception(e)
