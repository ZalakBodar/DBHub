from db_connection import get_connection

conn = get_connection()

cursor = conn.cursor()

cursor.execute("""
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE'
""")

for row in cursor.fetchall():
    print(row)

conn.close() 