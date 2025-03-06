import pymysql 

def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            port=3307,
            password='',
            database='etl'
        )
        if connection.open:
            print("Database connection successful")
            return connection
    except Error as e:
        print(f"Database connection failed: {e}")
        raise

