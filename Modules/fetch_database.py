def fetch_db_mysql(connection, database):
    cursor = connection.cursor()

    database_info_str = f"Server/Tool : MySQL\n"
    database_info_str += f"📚 DATABASE: **{database}**\n"
    database_info_str += "=====================================\n\n"

    # Step 1: List all tables
    cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{database}';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        database_info_str += f"🗂️ TABLE: **{table}**\n"

        # Step 2: Columns
        database_info_str += "  📌 Columns:\n"
        cursor.execute(f"""
            SELECT column_name, column_type, is_nullable, column_key, extra, column_default
            FROM information_schema.columns
            WHERE table_schema = '{database}' AND table_name = '{table}';
        """)
        for col in cursor.fetchall():
            col_name, col_type, nullable, key, extra, default = col
            database_info_str += (
                f"    • `{col_name}` ({col_type})\n"
                f"       └── Nullable: {'Yes' if nullable == 'YES' else 'No'} | "
                f"Key: {key or 'None'} | Extra: {extra or 'None'} | "
                f"Default: {default if default is not None else 'None'}\n"
            )

        # Step 3: Primary Key
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = '{table}' AND constraint_name = 'PRIMARY' AND table_schema = '{database}';
        """)
        pk = cursor.fetchall()
        if pk:
            pk_list = ', '.join([row[0] for row in pk])
            database_info_str += f"  🔑 Primary Key: {pk_list}\n"

        # Step 4: Foreign Keys
        cursor.execute(f"""
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = '{database}' AND table_name = '{table}' AND referenced_table_name IS NOT NULL;
        """)
        fk = cursor.fetchall()
        if fk:
            database_info_str += "  🔗 Foreign Keys:\n"
            for col, ref_table, ref_col in fk:
                database_info_str += f"    • `{col}` → {ref_table}({ref_col})\n"
        else:
            database_info_str += "  🔗 Foreign Keys: None\n"

        # Step 5: Unique Constraints
        cursor.execute(f"""
            SELECT DISTINCT INDEX_NAME, COLUMN_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}' AND NON_UNIQUE = 0 AND INDEX_NAME != 'PRIMARY';
        """)
        uniques = cursor.fetchall()
        if uniques:
            database_info_str += "  🔒 Unique Constraints:\n"
            for index, column in uniques:
                database_info_str += f"    • `{column}` (Index: {index})\n"
        else:
            database_info_str += "  🔒 Unique Constraints: None\n"

        # Step 6: Indexes
        cursor.execute(f"SHOW INDEX FROM {table};")
        indexes = cursor.fetchall()
        if indexes:
            database_info_str += "  📈 Indexes:\n"
            for idx in indexes:
                index_name = idx[2]
                column_name = idx[4]
                unique = 'No' if idx[1] else 'Yes'
                database_info_str += f"    • {index_name} on `{column_name}` (Unique: {unique})\n"
        else:
            database_info_str += "  📈 Indexes: None\n"

        # Step 7: Check Constraints
        cursor.execute(f"""
            SELECT CONSTRAINT_NAME, CHECK_CLAUSE
            FROM information_schema.check_constraints
            WHERE CONSTRAINT_SCHEMA = '{database}';
        """)
        checks = cursor.fetchall()
        if checks:
            database_info_str += "  ✅ Check Constraints:\n"
            for name, clause in checks:
                database_info_str += f"    • {name}: {clause}\n"

        # Step 8: Triggers (optional)
        cursor.execute(f"SHOW TRIGGERS FROM {database} WHERE `Table` = '{table}';")
        triggers = cursor.fetchall()
        if triggers:
            database_info_str += "  ⚙️ Triggers:\n"
            for trg in triggers:
                database_info_str += f"    • {trg[0]}: {trg[1]} {trg[4]} ON {trg[2]}\n"
        else:
            database_info_str += "  ⚙️ Triggers: None\n"

        database_info_str += "\n-------------------------------------\n\n"

    return database_info_str



def fetch_db_sqlite(connection, database):
    cursor = connection.cursor()
    database_info_str = f"Server/Tool : SQLite\n"
    database_info_str += f"📚 DATABASE: **{database}**\n"
    database_info_str += "=====================================\n\n"

    # Step 1: List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        database_info_str += f"🗂️ TABLE: **{table}**\n"

        # Step 2: Columns (PRAGMA table_info)
        database_info_str += "  📌 Columns:\n"
        cursor.execute(f"PRAGMA table_info('{table}');")
        for col in cursor.fetchall():
            cid, name, col_type, notnull, default_value, pk = col
            database_info_str += (
                f"    • `{name}` ({col_type})\n"
                f"       └── Nullable: {'No' if notnull else 'Yes'} | "
                f"Primary Key: {'Yes' if pk else 'No'} | "
                f"Default: {default_value if default_value is not None else 'None'}\n"
            )

        # Step 3: Foreign Keys
        cursor.execute(f"PRAGMA foreign_key_list('{table}');")
        fk = cursor.fetchall()
        if fk:
            database_info_str += "  🔗 Foreign Keys:\n"
            for row in fk:
                id_, seq, col, ref_table, ref_col, on_update, on_delete, match = row
                database_info_str += f"    • `{col}` → {ref_table}({ref_col})\n"
        else:
            database_info_str += "  🔗 Foreign Keys: None\n"

        # Step 4: Indexes
        cursor.execute(f"PRAGMA index_list('{table}');")
        indexes = cursor.fetchall()
        if indexes:
            database_info_str += "  📈 Indexes:\n"
            for idx in indexes:
                index_name = idx[1]
                unique = 'Yes' if idx[2] else 'No'
                cursor.execute(f"PRAGMA index_info('{index_name}');")
                columns = cursor.fetchall()
                for colinfo in columns:
                    database_info_str += f"    • {index_name} on `{colinfo[2]}` (Unique: {unique})\n"
        else:
            database_info_str += "  📈 Indexes: None\n"

        # Step 5: Check Constraints (No direct PRAGMA; parse from sqlite_master)
        cursor.execute(f"""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='{table}';
        """)
        row = cursor.fetchone()
        if row and "CHECK" in row[0].upper():
            database_info_str += "  ✅ Check Constraints (parsed from SQL):\n"
            lines = row[0].split('\n')
            for line in lines:
                if "CHECK" in line.upper():
                    database_info_str += f"    • {line.strip()}\n"
        else:
            database_info_str += "  ✅ Check Constraints: None\n"

        # Step 6: Triggers
        cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='{table}';")
        triggers = cursor.fetchall()
        if triggers:
            database_info_str += "  ⚙️ Triggers:\n"
            for name, sql in triggers:
                database_info_str += f"    • {name}: {sql}\n"
        else:
            database_info_str += "  ⚙️ Triggers: None\n"

        database_info_str += "\n-------------------------------------\n\n"

    return database_info_str


def fetch_db_sqlserver(connection, database):
    cursor = connection.cursor()
    database_info_str = f"Server/Tool : Microsoft SQL Server (SSMS)\n"
    database_info_str += f"📚 DATABASE: **{database}**\n"
    database_info_str += "=====================================\n\n"

    # Step 1: List all tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        database_info_str += f"🗂️ TABLE: **{table}**\n"

        # Step 2: Columns
        database_info_str += "  📌 Columns:\n"
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}';
        """)
        for col in cursor.fetchall():
            col_name, data_type, nullable, default = col
            database_info_str += (
                f"    • `{col_name}` ({data_type})\n"
                f"       └── Nullable: {'Yes' if nullable == 'YES' else 'No'} | "
                f"Default: {default if default else 'None'}\n"
            )

        # Step 3: Primary Key
        cursor.execute(f"""
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
            WHERE t.CONSTRAINT_TYPE = 'PRIMARY KEY' AND t.TABLE_NAME = '{table}';
        """)
        pk = cursor.fetchall()
        if pk:
            pk_list = ', '.join([row[0] for row in pk])
            database_info_str += f"  🔑 Primary Key: {pk_list}\n"
        else:
            database_info_str += f"  🔑 Primary Key: None\n"

        # Step 4: Foreign Keys
        cursor.execute(f"""
            SELECT cu.COLUMN_NAME, pk.TABLE_NAME, pk.COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE cu
              ON rc.CONSTRAINT_NAME = cu.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
              ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            WHERE cu.TABLE_NAME = '{table}';
        """)
        fk = cursor.fetchall()
        if fk:
            database_info_str += "  🔗 Foreign Keys:\n"
            for col, ref_table, ref_col in fk:
                database_info_str += f"    • `{col}` → {ref_table}({ref_col})\n"
        else:
            database_info_str += "  🔗 Foreign Keys: None\n"

        # Step 5: Unique Constraints
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE cu
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
              ON cu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'UNIQUE' AND cu.TABLE_NAME = '{table}';
        """)
        uniques = cursor.fetchall()
        if uniques:
            database_info_str += "  🔒 Unique Constraints:\n"
            for row in uniques:
                database_info_str += f"    • `{row[0]}`\n"
        else:
            database_info_str += "  🔒 Unique Constraints: None\n"

        # Step 6: Indexes
        cursor.execute(f"""
            SELECT ind.name AS index_name, col.name AS column_name, ind.is_unique
            FROM sys.indexes ind
            INNER JOIN sys.index_columns ic ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id
            INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
            INNER JOIN sys.tables t ON ind.object_id = t.object_id
            WHERE t.name = '{table}' AND ind.is_primary_key = 0;
        """)
        indexes = cursor.fetchall()
        if indexes:
            database_info_str += "  📈 Indexes:\n"
            for index_name, column_name, is_unique in indexes:
                unique = 'Yes' if is_unique else 'No'
                database_info_str += f"    • {index_name} on `{column_name}` (Unique: {unique})\n"
        else:
            database_info_str += "  📈 Indexes: None\n"

        # Step 7: Check Constraints
        cursor.execute(f"""
            SELECT cc.CONSTRAINT_NAME, cc.CHECK_CLAUSE
            FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
            JOIN INFORMATION_SCHEMA.CONSTRAINT_TABLE_USAGE ctu
              ON cc.CONSTRAINT_NAME = ctu.CONSTRAINT_NAME
            WHERE ctu.TABLE_NAME = '{table}';
        """)
        checks = cursor.fetchall()
        if checks:
            database_info_str += "  ✅ Check Constraints:\n"
            for name, clause in checks:
                database_info_str += f"    • {name}: {clause}\n"
        else:
            database_info_str += "  ✅ Check Constraints: None\n"

        # Step 8: Triggers
        cursor.execute(f"""
            SELECT tr.name, m.definition
            FROM sys.triggers tr
            JOIN sys.sql_modules m ON tr.object_id = m.object_id
            JOIN sys.tables t ON tr.parent_id = t.object_id
            WHERE t.name = '{table}';
        """)
        triggers = cursor.fetchall()
        if triggers:
            database_info_str += "  ⚙️ Triggers:\n"
            for name, definition in triggers:
                database_info_str += f"    • {name}: {definition[:100].strip()}...\n"
        else:
            database_info_str += "  ⚙️ Triggers: None\n"

        database_info_str += "\n-------------------------------------\n\n"

    return database_info_str



def fetch_db_postgresql(connection, database):
    cursor = connection.cursor()
    database_info_str = f"Server/Tool : Postgre SQL\n"
    database_info_str += f"📚 DATABASE: **{database}**\n"
    database_info_str += "=====================================\n\n"

    # Step 1: List all tables in 'public' schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        database_info_str += f"🗂️ TABLE: **{table}**\n"

        # Step 2: Columns
        database_info_str += "  📌 Columns:\n"
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{table}';
        """)
        for col in cursor.fetchall():
            name, dtype, nullable, default = col
            database_info_str += (
                f"    • `{name}` ({dtype})\n"
                f"       └── Nullable: {'Yes' if nullable == 'YES' else 'No'} | "
                f"Default: {default if default else 'None'}\n"
            )

        # Step 3: Primary Key
        cursor.execute(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_name = '{table}'
              AND tc.table_schema = 'public';
        """)
        pk = cursor.fetchall()
        if pk:
            pk_list = ', '.join([row[0] for row in pk])
            database_info_str += f"  🔑 Primary Key: {pk_list}\n"
        else:
            database_info_str += f"  🔑 Primary Key: None\n"

        # Step 4: Foreign Keys
        cursor.execute(f"""
            SELECT kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY'
              AND tc.table_name = '{table}'
              AND tc.table_schema = 'public';
        """)
        fk = cursor.fetchall()
        if fk:
            database_info_str += "  🔗 Foreign Keys:\n"
            for col, ref_table, ref_col in fk:
                database_info_str += f"    • `{col}` → {ref_table}({ref_col})\n"
        else:
            database_info_str += "  🔗 Foreign Keys: None\n"

        # Step 5: Unique Constraints
        cursor.execute(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
              AND tc.table_name = '{table}'
              AND tc.table_schema = 'public';
        """)
        uniques = cursor.fetchall()
        if uniques:
            database_info_str += "  🔒 Unique Constraints:\n"
            for row in uniques:
                database_info_str += f"    • `{row[0]}`\n"
        else:
            database_info_str += "  🔒 Unique Constraints: None\n"

        # Step 6: Indexes
        cursor.execute(f"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = '{table}';
        """)
        indexes = cursor.fetchall()
        if indexes:
            database_info_str += "  📈 Indexes:\n"
            for name, definition in indexes:
                database_info_str += f"    • {name}: {definition}\n"
        else:
            database_info_str += "  📈 Indexes: None\n"

        # Step 7: Check Constraints
        cursor.execute(f"""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE contype = 'c' AND t.relname = '{table}';
        """)
        checks = cursor.fetchall()
        if checks:
            database_info_str += "  ✅ Check Constraints:\n"
            for name, clause in checks:
                database_info_str += f"    • {name}: {clause}\n"
        else:
            database_info_str += "  ✅ Check Constraints: None\n"

        # Step 8: Triggers
        cursor.execute(f"""
            SELECT trigger_name, event_manipulation, action_timing
            FROM information_schema.triggers
            WHERE event_object_table = '{table}';
        """)
        triggers = cursor.fetchall()
        if triggers:
            database_info_str += "  ⚙️ Triggers:\n"
            for name, event, timing in triggers:
                database_info_str += f"    • {name}: {timing} {event}\n"
        else:
            database_info_str += "  ⚙️ Triggers: None\n"

        database_info_str += "\n-------------------------------------\n\n"

    return database_info_str



# def convert_to_docs(database_info_str: str):
#     docs = []

#     # Split based on table separators
#     parts = database_info_str.split("\n-------------------------------------\n\n")

#     # First part → DB info only
#     db_info = parts[0].strip()
#     docs.append(Document(page_content=db_info, metadata={"type": "database"}))

#     # Each subsequent part → Table info
#     for table_block in parts[1:]:
#         table_block = table_block.strip()
#         if not table_block:
#             continue
#         # Extract table name
#         lines = table_block.splitlines()
#         table_name = lines[0].replace("🗂️ TABLE: **", "").replace("**", "").strip()
#         docs.append(
#             Document(
#                 page_content=table_block,
#                 metadata={"type": "table", "table_name": table_name}
#             )
#         )

#     return docs
