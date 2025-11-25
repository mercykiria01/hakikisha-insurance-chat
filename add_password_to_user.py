"""
Add password to existing user in database
"""
import pyodbc
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

def add_password_to_user(email, password):
    """Add password to existing user"""
    try:
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get customer info (remains the same)
        cursor.execute("""
            SELECT CustomerID, CustomerName, PhoneNumber
            FROM Customers
            WHERE Email = ?
        """, (email,))
        
        customer = cursor.fetchone()
        
        if not customer:
            print(f"❌ Customer not found: {email}")
            return False
        
        customer_id = customer[0]
        customer_name = customer[1]
        
        print(f"📋 Found customer: {customer_name} (ID: {customer_id})")
        
        # Check if CustomerAuth record exists (remains the same)
        cursor.execute("""
            SELECT AuthID FROM CustomerAuth WHERE CustomerID = ?
        """, (customer_id,))
        
        auth_exists = cursor.fetchone()
        
        if auth_exists:
            # Update existing record (Correct and functional)
            cursor.execute("""
                UPDATE CustomerAuth
                SET HashedPassword = ?,
                    LastLogin = GETDATE()
                WHERE CustomerID = ?
            """, (password_hash, customer_id))
            print(f"✅ Password updated for {email}")
        else:
            # Create new CustomerAuth record (CRITICAL FIX APPLIED HERE)
            # NOTE: We use placeholders for CustomerID, HashedPassword, OTPAttempts, and IsLocked
            cursor.execute("""
                INSERT INTO CustomerAuth (
                    CustomerID,
                    HashedPassword,
                    OTPAttempts,
                    IsLocked,
                    CreatedDate,
                    LastLogin
                )
                -- 4 placeholders used here: ?, ?, ?, ?
                VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
            """, (customer_id, password_hash, 0, 0)) # <--- ONLY 4 VALUES passed now!
            
            print(f"✅ Password created for {email}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Success! You can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Main script
if __name__ == "__main__":
    print("=" * 60)
    print("ADD PASSWORD TO EXISTING USER")
    print("=" * 60)
    
    # Enter user details
    email = input("\nEnter user email: ").strip()
    password = input("Enter new password (min 8 chars): ").strip()
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
    else:
        add_password_to_user(email, password)