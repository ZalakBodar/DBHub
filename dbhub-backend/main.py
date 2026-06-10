from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_connection import get_connection
import pyodbc
from typing import Optional
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from pydantic import BaseModel

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
    username: Optional[str] = ""
    password: Optional[str] = ""
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

    global SCHEMA_CACHE

    if SCHEMA_CACHE:
        return SCHEMA_CACHE

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    ORDER BY TABLE_NAME
    """)

    rows = cursor.fetchall()

    conn.close()

    schema = {}

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

    SCHEMA_CACHE = schema_text

    return schema_text

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

    cursor.execute("SELECT * FROM Connectors")

    columns = [column[0] for column in cursor.description]

    data = []

    for row in cursor.fetchall():

        connector = dict(zip(columns, row))

    try:
        print(
            f"Host={connector.host}, "
            f"Port={connector.port}, "
            f"Database={connector.database}"
        )
        test_conn = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER=tcp:{connector['Host']},{connector['Port']};"
            f"DATABASE={connector['DatabaseName']};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;",
            timeout=3
        )

        cursor_test = test_conn.cursor()

        cursor_test.execute("SELECT DB_NAME()")

        actual_db = cursor_test.fetchone()[0]

        if actual_db.lower() == connector["DatabaseName"].lower():

            connector["Status"] = "Active"

        else:

            connector["Status"] = "Inactive"

        test_conn.close()

    except:

   
        connector["Status"] = "Inactive"

        data.append(connector)

    conn.close()

    return data
@app.post("/connectors")
def add_connector(connector: Connector):

    if (
        connector.name.strip() == "" or
        connector.host.strip() == "" or
        connector.database.strip() == ""
    ):
        return {
            "success": False,
            "message": "Connector Name, Host and Database Name are required"
        }

    # -----------------------------------
    # TEST CONNECTION BEFORE SAVE
    # -----------------------------------

    try:

        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={connector.host};"
            f"DATABASE={connector.database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

        test_conn = pyodbc.connect(
            conn_str,
            timeout=5
        )

        test_conn.close()

    except Exception as e:

        return {
            "success": False,
            "message": f"Cannot connect: {str(e)}"
        }

    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------
    # CHECK DUPLICATE NAME
    # -----------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM Connectors
        WHERE Name = ?
        """,
        connector.name
    )

    exists = cursor.fetchone()[0]

    if exists > 0:

        conn.close()

        return {
            "success": False,
            "message": "Connector already exists"
        }

    # -----------------------------------
    # SAVE CONNECTOR
    # -----------------------------------

    try:

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
                Status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            connector.name,
            connector.db_type,
            connector.host,
            connector.port,
            connector.username,
            connector.password,
            connector.database,
            "Active"
        )

        conn.commit()

        activities.insert(
            0,
            f"Connector {connector.name} added"
        )

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
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)

    tables = []

    for row in cursor.fetchall():
        tables.append(row[0])

    conn.close()

    return tables



@app.get("/metadata/{table_name}")
def get_metadata(table_name: str):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        c.COLUMN_NAME AS column_name,
        c.DATA_TYPE AS data_type,
        c.IS_NULLABLE AS nullable,
        c.CHARACTER_MAXIMUM_LENGTH AS max_length,

        CASE
            WHEN k.COLUMN_NAME IS NOT NULL
            THEN 'YES'
            ELSE 'NO'
        END AS primary_key

    FROM INFORMATION_SCHEMA.COLUMNS c

    LEFT JOIN
    (
        SELECT
            KU.TABLE_NAME,
            KU.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KU
            ON TC.CONSTRAINT_NAME = KU.CONSTRAINT_NAME
        WHERE TC.CONSTRAINT_TYPE='PRIMARY KEY'
    ) k

    ON c.TABLE_NAME = k.TABLE_NAME
    AND c.COLUMN_NAME = k.COLUMN_NAME

    WHERE c.TABLE_NAME = ?

    ORDER BY c.ORDINAL_POSITION
    """

    cursor.execute(query, table_name)

    rows = [
        dict(zip(
            [col[0] for col in cursor.description],
            row
        ))
        for row in cursor.fetchall()
    ]

    conn.close()

    return rows


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

    conn = get_connection()
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name}"

    cursor.execute(query)

    columns = [column[0] for column in cursor.description]

    data = []

    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))

    conn.close()

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

        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={connector.host};"
            f"DATABASE={connector.database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

        conn = pyodbc.connect(
            conn_str,
            timeout=5
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

    return activities[:10]


@app.get("/database-health")
def database_health():

    try:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("SELECT DB_NAME()")

        db_name = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "Connected",
            "database": db_name,
            "server": "SQL Server"
        }

    except Exception as e:

        return {
            "status": "Disconnected",
            "database": "-",
            "server": "-",
            "error": str(e)
        }
        
@app.post("/execute-query")
def execute_query(sql: SQLQuery):

    print("QUERY RECEIVED:")
    print(sql.query)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(sql.query)

    columns = [column[0] for column in cursor.description]

    rows = cursor.fetchall()

    print("ROWS:", len(rows))

    data = [
        dict(zip(columns, row))
        for row in rows
    ]

    conn.close()

    return data


    
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

    schema_text = get_relevant_schema(question)

    print("\nSCHEMA:")
    print(schema_text)

    prompt = f"""
You are an expert Microsoft SQL Server assistant.

Database Schema:
{schema_text}
Rules:

1. Use ONLY tables from schema.
2. Use ONLY columns from schema.
3. SQL Server syntax only.
4. Use TOP instead of LIMIT.
5. Generate JOINs when data exists in multiple tables.
6. Return ONLY SQL.
7. No markdown.
8. No explanation.
9. No comments.

Relationships:

Employees.DepartmentID -> Departments.DepartmentID

Example:

Question:
show employee name with department name

SQL:
SELECT
    e.Name,
    d.DepartmentName
FROM Employees e
JOIN Departments d
    ON e.DepartmentID = d.DepartmentID;
Example:

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

Question:
{question}
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

        conn = get_connection()

        cursor = conn.cursor()

        MAX_RETRIES = 3

        for attempt in range(MAX_RETRIES):

            try:

                cursor.execute(
                    generated_sql
                )

                break

            except Exception as sql_error:

                print(
                    f"\nATTEMPT {attempt + 1} FAILED"
                )

                print(sql_error)

                retry_prompt = f"""
        Question:
        {question}

        Schema:
        {schema_text}

        Failed SQL:
        {generated_sql}

        Error:
        {str(sql_error)}

        Return ONLY corrected SQL.
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

                print(
                    "\nRETRY SQL:"
                )

                print(
                    generated_sql
                )

                is_valid, message = validate_sql(
                    generated_sql
                )

                if not is_valid:

                    return {
                        "error": message
                    }

        else:

            return {
                "error":
                "AI failed after 3 attempts"
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

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        FK.TABLE_NAME AS child_table,
        CU.COLUMN_NAME AS child_column,

        PK.TABLE_NAME AS parent_table,
        PT.COLUMN_NAME AS parent_column

    FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS C

    INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS FK
        ON C.CONSTRAINT_NAME = FK.CONSTRAINT_NAME

    INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS PK
        ON C.UNIQUE_CONSTRAINT_NAME = PK.CONSTRAINT_NAME

    INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE CU
        ON C.CONSTRAINT_NAME = CU.CONSTRAINT_NAME

    INNER JOIN
    (
        SELECT *
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    ) PT
        ON PT.CONSTRAINT_NAME = PK.CONSTRAINT_NAME

    """

    cursor.execute(query)

    rows = [
        dict(zip(
            [c[0] for c in cursor.description],
            row
        ))
        for row in cursor.fetchall()
    ]

    conn.close()

    return rows

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