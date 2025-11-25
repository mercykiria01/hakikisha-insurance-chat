import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# Connection string
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

print("🔌 Testing database connection...")
print(f"Server: {os.getenv('DB_SERVER')}")
print(f"Database: {os.getenv('DB_DATABASE')}")

try:
    conn = pyodbc.connect(conn_str, timeout=10)
    print("✅ Database connection successful!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"✅ SQL Server version: {row[0][:50]}...")
    
    # Test your functions
    print("\n🧪 Testing database functions...")
    
    # Test 1: Check if tables exist
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✅ Found {len(tables)} tables: {', '.join(tables[:5])}...")
    
    # Test 2: Check if functions exist
    cursor.execute("""
        SELECT ROUTINE_NAME 
        FROM INFORMATION_SCHEMA.ROUTINES 
        WHERE ROUTINE_TYPE = 'FUNCTION'
        ORDER BY ROUTINE_NAME
    """)
    functions = [row[0] for row in cursor.fetchall()]
    print(f"✅ Found {len(functions)} functions: {', '.join(functions[:5])}...")
    
    # Test 3: Try to get a policy (if you have data)
    cursor.execute("SELECT TOP 1 * FROM Policies")
    policy = cursor.fetchone()
    if policy:
        print(f"✅ Sample policy found: {policy[1] if len(policy) > 1 else 'N/A'}")
    else:
        print("⚠️ No policies in database yet")
    
    cursor.close()
    conn.close()
    print("\n✅ All database tests passed!")
    
except pyodbc.Error as e:
    print(f"❌ Database connection failed!")
    print(f"Error: {e}")
    print("\n🔧 Troubleshooting tips:")
    print("1. Check your .env file has correct credentials")
    print("2. Verify your IP is allowed in Azure SQL firewall")
    print("3. Check if ODBC Driver 18 is installed")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")