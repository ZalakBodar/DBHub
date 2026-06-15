from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_connection import get_connection
from fastapi.responses import JSONResponse
import pyodbc
import oracledb
import psycopg2
from typing import Optional
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from datetime import datetime
import os
print("RUNNING FILE =", __file__)
print("CURRENT DIRECTORY =", os.getcwd())


SCHEMA_CACHE = ""
app = FastAPI()

# --------------------------------------------------
# CORS
# --------------------------------------------------
llm = ChatOpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    model="qwen2.5-coder-3b-instruct",
    temperature=0
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Models
# --------------------------------------------------


class Connector(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    database: str


class User(BaseModel):
    name: str
    email: str
    role: str
    
class UpdateUser(BaseModel):
    name: str
    email: str
    role: str
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
    
class SQLQuery(BaseModel):
    query: str
    
class AIQuestion(BaseModel):
    question: str
    
class AIRequest(BaseModel):
    question: str

class MetadataDescription(BaseModel):

    connector_id: int
    table_name: str
    column_name: str
    description: str
# -----------------------------
# SQL Validation Function
# -----------------------------

def validate_sql(sql):

    sql_upper = sql.upper().strip()

    dangerous = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "MERGE",
        "EXEC",
        "EXECUTE",
        "CREATE"
    ]

    for keyword in dangerous:

        if keyword in sql_upper:

            return False, f"{keyword} not allowed"

    return True, "Valid"


def get_relevant_schema(question):

    full_schema = get_schema()

    question = question.lower()

    tables = full_schema.split("\n")

    relevant = []

    keywords = {
        "users": ["user", "users"],
        "employees": ["employee", "employees", "salary", "department"],
        "connectors": ["connector", "connectors", "database", "host", "port"]
    }

    for table in tables:

        lower_table = table.lower()

        for _, words in keywords.items():

            if any(word in question for word in words):

                if any(word in lower_table for word in words):

                    relevant.append(table)

    if relevant:

        return "\n".join(relevant)

    return full_schema
# --------------------------------------------------
# In Memory Storage
# --------------------------------------------------

connectors = []
activities = []
query_history = []



def get_schema():

    connector = get_active_connector_details()

    if not connector:
        return ""

    db_type = connector[1]
    host = connector[2]
    port = connector[3]
    username = connector[4]
    password = connector[5]
    database = connector[6]

    schema = {}

    # MSSQL
    if db_type == "MSSQL":

        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

        cursor = conn.cursor()

        cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_NAME
        """)

    # PostgreSQL
    elif db_type == "POSTGRESQL":

        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )

        cursor = conn.cursor()

        cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema='public'
        ORDER BY table_name
        """)

    # Oracle
    elif db_type == "ORACLE":

        conn = oracledb.connect(
            user=username,
            password=password,
            dsn=f"{host}:{port}/{database}"
        )

        cursor = conn.cursor()

        cursor.execute("""
        SELECT table_name, column_name
        FROM user_tab_columns
        ORDER BY table_name
        """)

    rows = cursor.fetchall()

    conn.close()

    for table, column in rows:

        if table not in schema:
            schema[table] = []

        schema[table].append(column)

    schema_text = ""

    for table, columns in schema.items():

        schema_text += (
            f"{table}("
            + ",".join(columns)
            + ")\n"
        )

    return schema_text

def get_metadata_descriptions():

    connector = get_active_connector_details()

    if not connector:
        return ""

    connector_id = connector[0]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            TableName,
            ColumnName,
            Description
        FROM Metadata
        WHERE ConnectorId = ?
          AND Description IS NOT NULL
    """, connector_id)

    rows = cursor.fetchall()

    conn.close()

    text = ""

    for row in rows:

        text += (
            f"\nTable: {row[0]}"
            f"\nColumn: {row[1]}"
            f"\nDescription: {row[2]}\n"
        )

    return text

def get_active_connector_details():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Id,
            DbType,
            Host,
            Port,
            Username,
            Password,
            DatabaseName
        FROM Connectors
        WHERE IsActive = 1
    """)

    row = cursor.fetchone()

    conn.close()

    return row
# --------------------------------------------------
# Home
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "DBHub Backend Running"
    }


# --------------------------------------------------
# Database Info
# --------------------------------------------------

@app.get("/db-info")
def db_info():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DB_NAME()")

    db_name = cursor.fetchone()[0]

    conn.close()

    return {
        "database": db_name
    }


# --------------------------------------------------
# Connectors
# --------------------------------------------------

@app.get("/connectors")
def get_connectors():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Id,
            Name,
            DbType,
            Host,
            Port,
            Username,
            DatabaseName,
            Status,
            IsActive,
            LastChecked,
            UpdatedAt
        FROM Connectors
    """)

    columns = [column[0] for column in cursor.description]

    connectors = []

    for row in cursor.fetchall():

        connectors.append(
            dict(zip(columns, row))
        )

    conn.close()

    return connectors

@app.post("/connectors")
def add_connector(connector: Connector):

    print("Received:", connector)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Check duplicate name
        cursor.execute(
            "SELECT COUNT(*) FROM Connectors WHERE Name = ?",
            connector.name
        )

        if cursor.fetchone()[0] > 0:

            return {
                "success": False,
                "message": "Connector name already exists"
            }

        if connector.db_type == "MSSQL":

             test_conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={connector.host};"
                f"DATABASE={connector.database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )

        elif connector.db_type == "ORACLE":

            test_conn = oracledb.connect(
                user=connector.username,
                password=connector.password,
                dsn=f"{connector.host}:{connector.port}/{connector.database}"
            )

        elif connector.db_type == "POSTGRESQL":

            test_conn = psycopg2.connect(
                host=connector.host,
                port=connector.port,
                database=connector.database,
                user=connector.username,
                password=connector.password
            )

        test_conn.close()

        # Save connector
        cursor.execute(
            """
            INSERT INTO Connectors
            (
                Name,
                DbType,
                Host,
                Port,
                Username,
                Password,
                DatabaseName,
                Status,
                LastChecked,
                UpdatedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            connector.name,
            connector.db_type,
            connector.host,
            connector.port,
            connector.username,
            connector.password,
            connector.database,
            "Active",
            datetime.now(),
            datetime.now()
        )

        conn.commit()
        cursor.execute(
            """
            INSERT INTO QueryHistory
            (
                Question,
                SQLQuery
            )
            VALUES (?, ?)
            """,
            f"Connector {connector.name} created",
            f"{connector.db_type} connector added"
        )

        conn.commit()

        return {
            "success": True,
            "message": "Connector Saved Successfully"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        conn.close()

# --------------------------------------------------
# Tables
# --------------------------------------------------


@app.get("/tables")
def get_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Id
        FROM Connectors
        WHERE IsActive = 1
    """)

    active = cursor.fetchone()

    if not active:
        return []

    connector_id = active[0]

    cursor.execute("""
        SELECT DISTINCT TableName
        FROM Metadata
        WHERE ConnectorId = ?
        ORDER BY TableName
    """, connector_id)

    tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    return tables

@app.get("/metadata/{table_name}")
def get_metadata(table_name: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Id
        FROM Connectors
        WHERE IsActive = 1
    """)

    active = cursor.fetchone()

    if not active:
        return []

    connector_id = active[0]

    cursor.execute("""
        SELECT
            ColumnName,
            DataType,
            Description
        FROM Metadata
        WHERE ConnectorId = ?
        AND TableName = ?
    """, (connector_id, table_name))

    rows = []

    for row in cursor.fetchall():

        rows.append({
            "column_name": row[0],
            "data_type": row[1],
            "description": row[2],
            "nullable": "",
            "max_length": "",
            "primary_key": "NO"
        })

    conn.close()

    return rows

@app.put("/metadata/description")
def save_metadata_description(data: MetadataDescription):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE Metadata
            SET Description = ?
            WHERE ConnectorId = ?
            AND TableName = ?
            AND ColumnName = ?
        """,
        (
            data.description,
            data.connector_id,
            data.table_name,
            data.column_name
        ))

        conn.commit()

        return {
            "success": True,
            "message": "Description Saved"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        conn.close()
@app.post("/metadata/save-description")
def save_description(data: MetadataDescription):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE Metadata
            SET Description = ?
            WHERE ConnectorId = ?
              AND TableName = ?
              AND ColumnName = ?
        """,
        (
            data.description,
            data.connector_id,
            data.table_name,
            data.column_name
        ))

        conn.commit()

        return {
            "success": True,
            "message": "Description saved"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()
@app.get("/active-connector")
def get_active_connector():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 1 Id, Name, DbType
        FROM Connectors
        WHERE IsActive = 1
    """)

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "db_type": row[2]
    }
@app.get("/ai-context")
def get_ai_context():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ConnectorId,
            TableName,
            ColumnName,
            Description
        FROM Metadata
        WHERE Description IS NOT NULL
    """)

    rows = cursor.fetchall()

    result = []

    for row in rows:
        result.append({
            "connector_id": row[0],
            "table_name": row[1],
            "column_name": row[2],
            "description": row[3]
        })

    conn.close()

    return result

# --------------------------------------------------
# Columns
# --------------------------------------------------

@app.get("/columns/{table_name}")
def get_columns(table_name: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = ?
""", table_name)

    columns = []

    for row in cursor.fetchall():

       columns.append({
    "column_name": row.COLUMN_NAME,
    "data_type": row.DATA_TYPE,
    "nullable": row.IS_NULLABLE,
    "max_length": row.CHARACTER_MAXIMUM_LENGTH
})

    conn.close()

    return columns


# --------------------------------------------------
# Data Viewer
# --------------------------------------------------

@app.get("/data/{table_name}")
def get_table_data(table_name: str):

    connector = get_active_connector_details()

    if not connector:
        return []

    db_type = connector[1]
    host = connector[2]
    port = connector[3]
    username = connector[4]
    password = connector[5]
    database = connector[6]

    data = []

    # MSSQL
    if db_type == "MSSQL":

        source_conn = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

        cursor = source_conn.cursor()

        cursor.execute(
            f"SELECT TOP 100 * FROM {table_name}"
        )

        columns = [
            column[0]
            for column in cursor.description
        ]

        for row in cursor.fetchall():

            data.append(
                dict(zip(columns, row))
            )

        source_conn.close()

    # ORACLE
    elif db_type == "ORACLE":

        source_conn = oracledb.connect(
            user=username,
            password=password,
            dsn=f"{host}:{port}/{database}"
        )

        cursor = source_conn.cursor()

        cursor.execute(
            f"SELECT * FROM {table_name}"
        )

        columns = [
            col[0]
            for col in cursor.description
        ]

        for row in cursor.fetchall():

            data.append(
                dict(zip(columns, row))
            )

        source_conn.close()

    # POSTGRESQL
    elif db_type == "POSTGRESQL":

        source_conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )

        cursor = source_conn.cursor()

        cursor.execute(
            f'SELECT * FROM "{table_name}"'
        )

        columns = [
            col[0]
            for col in cursor.description
        ]

        for row in cursor.fetchall():

            data.append(
                dict(zip(columns, row))
            )

        source_conn.close()

    return data


# --------------------------------------------------
# Test Users
# --------------------------------------------------

@app.get("/test-users")
def test_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users")

    columns = [column[0] for column in cursor.description]

    conn.close()

    return {
        "columns": columns
    }


# --------------------------------------------------
# Get Users
# --------------------------------------------------

@app.get("/users")
def get_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users")

    columns = [column[0] for column in cursor.description]

    users = []

    for row in cursor.fetchall():
        users.append(dict(zip(columns, row)))

    conn.close()

    return users


# --------------------------------------------------
# Add User
# --------------------------------------------------

@app.post("/users")
def add_user(user: User):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO Users
        (Name, Email, Role)
        VALUES (?, ?, ?)
        """,
        user.name,
        user.email,
        user.role
    )

    conn.commit()
    conn.close()
    
    activities.insert(
    0,
    f"User {user.name} created"
)

    return {
        "message": "User created successfully"
    }





# --------------------------------------------------
# Delete User
# --------------------------------------------------

@app.delete("/users/{user_id}")
def delete_user(user_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Users WHERE Id = ?",
        user_id
    )

    conn.commit()
    conn.close()

    activities.insert(
        0,
        f"User {user_id} deleted"
    )

    return {
        "message": "User deleted successfully"
    }

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UpdateUser):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Users
        SET Name = ?, Email = ?, Role = ?
        WHERE Id = ?
    """,
    user.name,
    user.email,
    user.role,
    user_id)

    conn.commit()
    conn.close()

    return {
        "message": "User updated successfully"
    }


# --------------------------------------------------
# Login
# --------------------------------------------------
@app.post("/login")
def login(login_data: LoginRequest):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Name, Email, Role, Password
        FROM Users
        WHERE Email = ?
    """, login_data.email)

    user = cursor.fetchone()

    conn.close()

    if not user:
        return {
            "success": False,
            "message": "User not found"
        }

    if user[3] != login_data.password:
        return {
            "success": False,
            "message": "Invalid password"
        }
        
        activities.insert(
    0,
    f"{user[0]} logged in"
)

    return {
        "success": True,
        "name": user[0],
        "email": user[1],
        "role": user[2]
    }
    
    
@app.delete("/connectors/{connector_id}")
def delete_connector(connector_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Connectors WHERE Id = ?",
        connector_id
    )

    conn.commit()
    conn.close()

    activities.insert(
        0,
        f"Connector {connector_id} deleted"
    )

    return {
        "message": "Connector Deleted"
    }
    


@app.post("/test-connection")
def test_connection(connector: Connector):

    try:

        if connector.db_type == "MSSQL":

            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={connector.host};"
                f"DATABASE={connector.database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;",
                timeout=5
            )

            conn.close()

        elif connector.db_type == "ORACLE":

            conn = oracledb.connect(
                user=connector.username,
                password=connector.password,
                dsn=f"{connector.host}:{connector.port}/{connector.database}"
            )

            conn.close()
        elif connector.db_type == "POSTGRESQL":

            conn = psycopg2.connect(
                host=connector.host,
                port=connector.port,
                database=connector.database,
                user=connector.username,
                password=connector.password
            )

            conn.close()

        return {
            "success": True,
            "message": "Connection Successful"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }
        
@app.post("/connectors/refresh-status")
def refresh_connector_status():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Id,
            DbType,
            Host,
            Port,
            Username,
            Password,
            DatabaseName
        FROM Connectors
    """)

    connectors = cursor.fetchall()

    for connector in connectors:

        connector_id = connector[0]
        db_type = connector[1]
        host = connector[2]
        port = connector[3]
        username = connector[4]
        password = connector[5]
        database = connector[6]

        try:

            if db_type == "MSSQL":

                test_conn = pyodbc.connect(
                    "DRIVER={ODBC Driver 18 for SQL Server};"
                    f"SERVER={host};"
                    f"DATABASE={database};"
                    "Trusted_Connection=yes;"
                    "TrustServerCertificate=yes;",
                    timeout=5
                )

            elif db_type == "ORACLE":

                test_conn = oracledb.connect(
                    user=username,
                    password=password,
                    dsn=f"{host}:{port}/{database}"
                )

            elif db_type == "POSTGRESQL":

                test_conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password
                )

            test_conn.close()
            status = "Active"

        except Exception as e:

            print("Refresh Error:", e)
            status = "Failed"

        cursor.execute(
            """
            UPDATE Connectors
            SET
                Status = ?,
                LastChecked = ?
            WHERE Id = ?
            """,
            (
                status,
                datetime.now(),
                connector_id
            )
        )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Connector statuses refreshed"
    }
@app.post("/connectors/activate/{connector_id}")
def activate_connector(connector_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Get connector name before activating
        cursor.execute(
            """
            SELECT Name
            FROM Connectors
            WHERE Id = ?
            """,
            connector_id
        )

        row = cursor.fetchone()

        connector_name = (
            row[0]
            if row
            else f"Connector {connector_id}"
        )

        # Deactivate all connectors
        cursor.execute("""
            UPDATE Connectors
            SET IsActive = 0
        """)

        # Activate selected connector
        cursor.execute(
            """
            UPDATE Connectors
            SET IsActive = 1
            WHERE Id = ?
            """,
            connector_id
        )

        # Save activity
        cursor.execute(
            """
            INSERT INTO QueryHistory
            (
                Question,
                SQLQuery
            )
            VALUES (?, ?)
            """,
            f"Connector {connector_name} activated",
            "ACTIVATE_CONNECTOR"
        )

        conn.commit()

        return {
            "success": True,
            "message": "Connector Activated"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        conn.close()
@app.post("/connectors/refresh/{connector_id}")
def refresh_connector_status(connector_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Host,
               Port,
               DatabaseName,
               Username,
               Password,
               DbType
        FROM Connectors
        WHERE Id = ?
    """, connector_id)

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "Connector not found"
        }

    try:

        test_conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={row.Host},{row.Port};"
            f"DATABASE={row.DatabaseName};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;",
            timeout=5
        )

        test_conn.close()

        cursor.execute("""
            UPDATE Connectors
            SET Status = 'Active'
            WHERE Id = ?
        """, connector_id)

    except:

        cursor.execute("""
            UPDATE Connectors
            SET Status = 'Failed'
            WHERE Id = ?
        """, connector_id)

    conn.commit()
    conn.close()

    return {
        "success": True
    }
@app.post("/metadata/extract/{connector_id}")
def extract_metadata(connector_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Get connector details
        cursor.execute("""
            SELECT
                Id,
                DbType,
                Host,
                Port,
                Username,
                Password,
                DatabaseName
            FROM Connectors
            WHERE Id = ?
        """, connector_id)

        connector = cursor.fetchone()

        if not connector:
            return {
                "success": False,
                "message": "Connector not found"
            }

        db_type = connector[1]
        host = connector[2]
        port = connector[3]
        username = connector[4]
        password = connector[5]
        database = connector[6]

        metadata_rows = []

        # ==========================
        # ORACLE
        # ==========================
        if db_type == "ORACLE":

            source_conn = oracledb.connect(
                user=username,
                password=password,
                dsn=f"{host}:{port}/{database}"
            )

            source_cursor = source_conn.cursor()

            # Debug
            source_cursor.execute("""
                SELECT USER,
                       SYS_CONTEXT('USERENV','CON_NAME')
                FROM DUAL
            """)

            print("CURRENT SESSION =", source_cursor.fetchone())

            source_cursor.execute("""
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    DATA_TYPE
                FROM ALL_TAB_COLUMNS
                WHERE OWNER = 'SYSTEM'
                  AND TABLE_NAME IN ('EMPLOYEES', 'DEPARTMENTS')
                ORDER BY TABLE_NAME, COLUMN_ID
            """)

            metadata_rows = source_cursor.fetchall()

            print("ROWS FOUND =", len(metadata_rows))

            for row in metadata_rows:
                print(row)

            source_conn.close()

        # ==========================
        # MSSQL
        # ==========================
        elif db_type == "MSSQL":

            print("CONNECTING TO MSSQL")

            source_conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={host};"
                f"DATABASE={database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )

            source_cursor = source_conn.cursor()

            source_cursor.execute("""
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                ORDER BY TABLE_NAME
            """)

            metadata_rows = source_cursor.fetchall()

            print("MSSQL ROWS FOUND =", len(metadata_rows))

            for row in metadata_rows[:10]:
                print(row)

            source_conn.close()
        # ==========================
        # POSTGRESQL
        # ==========================
        elif db_type == "POSTGRESQL":

            source_conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )

            source_cursor = source_conn.cursor()

            source_cursor.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            metadata_rows = source_cursor.fetchall()

            source_conn.close()

        # ==========================
        # DELETE OLD METADATA
        # ==========================
        cursor.execute(
            "DELETE FROM Metadata WHERE ConnectorId = ?",
            connector_id
        )

        # ==========================
        # INSERT NEW METADATA
        # ==========================
        inserted_rows = 0

        for row in metadata_rows:

            cursor.execute("""
                INSERT INTO Metadata
                (
                    ConnectorId,
                    TableName,
                    ColumnName,
                    DataType
                )
                VALUES (?, ?, ?, ?)
            """,
            (
                connector_id,
                str(row[0]),
                str(row[1]),
                str(row[2])
            ))

            inserted_rows += 1

        conn.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM Metadata WHERE ConnectorId = ?",
            connector_id
        )

        total_rows = cursor.fetchone()[0]

        print("ROWS IN METADATA =", total_rows)

        return {
            "success": True,
            "rows": len(metadata_rows),
            "inserted_rows": inserted_rows,
            "message": "Metadata Extracted Successfully"
        }

    except Exception as e:

        print("ERROR =", str(e))

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        conn.close()
@app.get("/dashboard-stats")
def dashboard_stats():

    conn = get_connection()
    cursor = conn.cursor()

    # Total Tables
    cursor.execute("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE='BASE TABLE'
    """)
    total_tables = cursor.fetchone()[0]

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM Users")
    total_users = cursor.fetchone()[0]

    conn.close()

    return {
        "totalTables": total_tables,
        "totalUsers": total_users,
        "databaseName": "DBHubTest",
        "connectorType": "MSSQL"
    }
    
@app.get("/activities")
def get_activities():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 5 Question
        FROM QueryHistory
        ORDER BY Id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]

@app.get("/database-health")
def database_health():

    connector = get_active_connector()

    if not connector:

        return {
            "status": "Disconnected",
            "database": "-",
            "server": "-"
        }

    return {
        "status": "Connected",
        "database": connector["name"],
        "server": connector["db_type"]
    }
@app.post("/execute-query")
def execute_query(sql: SQLQuery):

    try:

        print("QUERY RECEIVED:")
        print(sql.query)

        connector = get_active_connector_details()

        if not connector:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "No active connector found"
                }
            )

        db_type = connector[1]
        host = connector[2]
        port = connector[3]
        username = connector[4]
        password = connector[5]
        database = connector[6]

        # MSSQL
        if db_type == "MSSQL":

            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={host};"
                f"DATABASE={database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )

        # PostgreSQL
        elif db_type == "POSTGRESQL":

            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )

        # Oracle
        elif db_type == "ORACLE":

            conn = oracledb.connect(
                user=username,
                password=password,
                dsn=f"{host}:{port}/{database}"
            )

        else:

            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Unsupported DB Type: {db_type}"
                }
            )

        cursor = conn.cursor()

        cursor.execute(sql.query)

        columns = [column[0] for column in cursor.description]

        rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        conn.close()

        return rows

    except Exception as e:

        print("QUERY ERROR:")
        print(str(e))

        return JSONResponse(
            status_code=400,
            content={
                "message": str(e)
            }
        )

    
@app.post("/generate-sql")
def generate_sql(data: AIRequest):

    question = data.question.lower()

    if "all users" in question:
        return {
            "sql": "SELECT * FROM Users"
        }
        

    elif "all tables" in question:
        return {
            "sql": """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            """
        }
    elif "employee" in question:
        return {
            "sql": "SELECT * FROM Users"
        }

    elif "all connectors" in question:
        return {
            "sql": "SELECT * FROM Connectors"
        }

    return {
        "sql": "Unable to generate SQL"
    }

@app.get("/query-history")
def get_query_history():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT TOP 50 *
        FROM QueryHistory
        ORDER BY Id DESC
        """
    )

    columns = [
        col[0]
        for col in cursor.description
    ]

    rows = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

    conn.close()

    return rows

@app.post("/refresh-schema")
def refresh_schema():

    global SCHEMA_CACHE

    SCHEMA_CACHE = ""

    get_schema()

    return {
        "message": "Schema refreshed"
    }
    

@app.post("/ask-ai")
def ask_ai(data: AIRequest):

    import time

    start_time = time.time()
    question = data.question.lower()
    connector = get_active_connector_details()

    if not connector:
        return {
            "error": "No active connector found"
        }

    db_type = connector[1]
    host = connector[2]
    port = connector[3]
    username = connector[4]
    password = connector[5]
    database = connector[6]
    schema_text = get_relevant_schema(question)
    metadata_text = get_metadata_descriptions()
    print("METADATA CONTEXT")
    print(metadata_text)

    print("================================")
    print("SCHEMA TEXT START")
    print(schema_text)
    print("SCHEMA TEXT END")
    print("================================")
    print("ACTIVE DB =", db_type)
    prompt = f"""
You are an expert database assistant.

Database Type:
{db_type}

Database Schema:
{schema_text}

Metadata Descriptions:
{metadata_text}

Rules:

1. Use ONLY tables from the schema.
2. Use ONLY columns from the schema.
3. Generate SQL for the active database type only.

If Database Type is MSSQL:
- Use TOP instead of LIMIT
- Use SQL Server syntax

If Database Type is POSTGRESQL:
- Use LIMIT
- Use PostgreSQL syntax

If Database Type is ORACLE:
- Use Oracle syntax
- Use FETCH FIRST N ROWS ONLY when limiting rows
- Use table names exactly as provided in schema

4. Generate JOINs when data exists in multiple tables.
5. Return ONLY SQL.
6. No markdown.
7. No explanation.
8. No comments.
9. Never invent tables or columns not present in schema.
10. Use metadata descriptions to understand column meanings.

Relationships:

Employees.DepartmentID -> Departments.DepartmentID

Examples:

Question:
show employee name with department name

SQL:
SELECT
    e.Name,
    d.DepartmentName
FROM Employees e
JOIN Departments d
    ON e.DepartmentID = d.DepartmentID;

Question:
show user names and roles

SQL:
SELECT Name, Role
FROM Users;

Question:
show employee names and departments

SQL:
SELECT Name, Department
FROM Employees;

Question:
count employees

SQL:
SELECT COUNT(*) AS TotalEmployees
FROM Employees;

User Question:
{question}

SQL:
"""

    try:

        response = llm.invoke(prompt)

        generated_sql = (
            response.content
            .replace("```sql", "")
            .replace("```", "")
            .strip()
        )

        sql_upper = generated_sql.upper()

        # Fix SHOW TABLES
        if "SHOW TABLES" in sql_upper:

            generated_sql = """
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
"""

        # Fix SP_HELP
        if "SP_HELP" in sql_upper:

            table_name = "Users"

            if "employee" in question:
                table_name = "Employees"

            elif "connector" in question:
                table_name = "Connectors"

            generated_sql = f"""
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='{table_name}'
"""

        # Fix LIMIT
        if "LIMIT 1" in generated_sql.upper():

            generated_sql = generated_sql.replace(
                "LIMIT 1",
                ""
            )

            if "TOP 1" not in generated_sql.upper():

                generated_sql = generated_sql.replace(
                    "SELECT",
                    "SELECT TOP 1",
                    1
                )

        print("\nQUESTION:")
        print(question)

        print("\nGENERATED SQL:")
        print(generated_sql)

        is_valid, message = validate_sql(
            generated_sql
        )

        if not is_valid:

            return {
                "error": message
            }

        if db_type == "MSSQL":

            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={host};"
                f"DATABASE={database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )

        elif db_type == "POSTGRESQL":

            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )

        elif db_type == "ORACLE":

            conn = oracledb.connect(
                user=username,
                password=password,
                dsn=f"{host}:{port}/{database}"
            )

        cursor = conn.cursor()

        MAX_RETRIES = 3

        for attempt in range(MAX_RETRIES):

            try:

                cursor.execute(generated_sql)

                break

            except Exception as sql_error:

                print(f"\nATTEMPT {attempt + 1} FAILED")
                print(sql_error)

                retry_prompt = f"""
        Question:
        {question}

        Database Type:
        {db_type}

        Schema:
        {schema_text}

        Metadata:
        {metadata_text}

        Failed SQL:
        {generated_sql}

        Error:
        {str(sql_error)}

            Rules:
        1. Return ONLY SQL.
        2. No explanation.
        3. No markdown.
        4. No comments.
        5. Generate valid {db_type} SQL.
        6. Use only tables and columns from schema.
        7. If the requested table does not exist, return:

        TABLE_NOT_FOUND

        8. Never substitute another table.

        SQL:
        """

                retry_response = llm.invoke(
                    retry_prompt
                )

                generated_sql = (
                    retry_response.content
                    .replace("```sql", "")
                    .replace("```", "")
                    .strip()
                )

                generated_sql = generated_sql.rstrip(";")

                print("\nRETRY SQL:")
                print(generated_sql)

                is_valid, message = validate_sql(
                    generated_sql
                )

                if not is_valid:

                    return {
                        "error": message
                    }

        else:

            return {
                "error": "AI failed after 3 attempts"
            }

        columns = [
            col[0]
            for col in cursor.description
        ]

        rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        print("SAVING TO QUERY HISTORY")
        print(question)
        print(generated_sql)

        history_conn = get_connection()
        history_cursor = history_conn.cursor()

        history_cursor.execute(
            """
            INSERT INTO QueryHistory
            (
                Question,
                SQLQuery
            )
            VALUES (?, ?)
            """,
            question,
            generated_sql
        )

        history_conn.commit()
        history_conn.close()

        return {
            "sql": generated_sql,
            "answer": rows,
            "count": len(rows),
            "executionTime": round(
                time.time() - start_time,
                2
            ),
            "explanation": f"Returned {len(rows)} record(s)"

        }

    except Exception as e:

                            return {
                                "error": str(e)
                            }
                
@app.get("/relationships")
def get_relationships():

    connector = get_active_connector_details()

    if not connector:
        return []

    db_type = connector[1]
    host = connector[2]
    port = connector[3]
    username = connector[4]
    password = connector[5]
    database = connector[6]

    try:

        if db_type == "MSSQL":

            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={host};"
                f"DATABASE={database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )

            query = """
            SELECT
                PK.TABLE_NAME AS parent_table,
                PT.COLUMN_NAME AS parent_column,
                FK.TABLE_NAME AS child_table,
                CU.COLUMN_NAME AS child_column
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS C
            INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS FK
                ON C.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
            INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS PK
                ON C.UNIQUE_CONSTRAINT_NAME = PK.CONSTRAINT_NAME
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE CU
                ON C.CONSTRAINT_NAME = CU.CONSTRAINT_NAME
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE PT
                ON PT.CONSTRAINT_NAME = PK.CONSTRAINT_NAME
            """

        elif db_type == "POSTGRESQL":

            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )

            query = """
            SELECT
                ccu.table_name AS parent_table,
                ccu.column_name AS parent_column,
                tc.table_name AS child_table,
                kcu.column_name AS child_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            """

        elif db_type == "ORACLE":

            conn = oracledb.connect(
                user=username,
                password=password,
                dsn=f"{host}:{port}/{database}"
            )

            query = """
            SELECT
                p.table_name AS parent_table,
                pc.column_name AS parent_column,
                c.table_name AS child_table,
                cc.column_name AS child_column
            FROM user_constraints c
            JOIN user_cons_columns cc
                ON c.constraint_name = cc.constraint_name
            JOIN user_constraints p
                ON c.r_constraint_name = p.constraint_name
            JOIN user_cons_columns pc
                ON p.constraint_name = pc.constraint_name
            WHERE c.constraint_type = 'R'
            """

        else:

            return []

        cursor = conn.cursor()

        cursor.execute(query)

        rows = [
            dict(
                zip(
                    [col[0].lower() for col in cursor.description],
                    row
                )
            )
            for row in cursor.fetchall()
        ]

        conn.close()

        return rows

    except Exception as e:

        return {
            "error": str(e)
        }

@app.get("/connector-count")
def connector_count():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM Connectors"
    )

    count = cursor.fetchone()[0]

    conn.close()

    return {"count": count}