import psycopg2

try:

    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="dbhub_postgres",
        user="postgres",
        password="Z@lak123"
    )

    print("CONNECTED SUCCESSFULLY")

    conn.close()

except Exception as e:

    print("ERROR:")
    print(e)