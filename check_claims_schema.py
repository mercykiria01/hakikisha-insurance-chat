"""
Check actual Claims table schema
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("=" * 80)
print("CLAIMS TABLE SCHEMA")
print("=" * 80)

cursor.execute("""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Claims'
    ORDER BY ORDINAL_POSITION
""")

for row in cursor.fetchall():
    nullable = "NULL" if row[3] == "YES" else "NOT NULL"
    length = f"({row[2]})" if row[2] else ""
    print(f"{row[0]:25} {row[1]}{length:15} {nullable}")

print("\n" + "=" * 80)
print("SAMPLE CLAIMS DATA")
print("=" * 80)

cursor.execute("SELECT TOP 3 * FROM Claims")

columns = [column[0] for column in cursor.description]
print("\nColumns:", ", ".join(columns))

rows = cursor.fetchall()
if rows:
    print(f"\nFound {len(rows)} claims:")
    for row in rows:
        print(f"\n{'-' * 80}")
        for i, col in enumerate(columns):
            print(f"  {col}: {row[i]}")
else:
    print("\n⚠️ No claims found in database")

cursor.close()
conn.close()