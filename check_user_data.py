"""
Check what policies and claims exist for a user - Updated for actual schema
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

def check_user_data(email):
    """Check policies and claims for a user"""
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print("=" * 80)
        print(f"DATA FOR USER: {email}")
        print("=" * 80)
        
        # Get customer info
        cursor.execute("""
            SELECT CustomerID, CustomerName, PolicyNumber, Email
            FROM Customers
            WHERE Email = ?
        """, (email,))
        
        customer = cursor.fetchone()
        
        if not customer:
            print(f"❌ Customer not found: {email}")
            return
        
        customer_id = customer[0]
        customer_name = customer[1]
        policy_number = customer[2]
        
        print(f"\n👤 CUSTOMER INFO:")
        print(f"   ID: {customer_id}")
        print(f"   Name: {customer_name}")
        print(f"   Email: {email}")
        print(f"   Policy Number: {policy_number}")
        
        # Check policies (using actual column names)
        cursor.execute("""
            SELECT 
                PolicyID,
                PolicyNumber,
                PolicyName,
                CoverageAmount,
                PremiumAmount,
                PolicyStatus,
                StartDate,
                EndDate
            FROM Policies
            WHERE CustomerID = ?
        """, (customer_id,))
        
        policies = cursor.fetchall()
        
        print(f"\n📋 POLICIES: {len(policies)} found")
        if policies:
            for policy in policies:
                print(f"   - {policy[1]} | {policy[2]} | KES {policy[3]:,.2f} coverage | Status: {policy[5]}")
        else:
            print("   ⚠️ No policies found for this customer")
        
        # Check claims (using actual column names)
        cursor.execute("""
            SELECT 
                c.ClaimID,
                c.ClaimNumber,
                c.ClaimType,
                c.ClaimAmount,
                c.ClaimStatus,
                c.ReportedDate,
                p.PolicyNumber
            FROM Claims c
            INNER JOIN Policies p ON c.PolicyID = p.PolicyID
            WHERE c.CustomerID = ?
        """, (customer_id,))
        
        claims = cursor.fetchall()
        
        print(f"\n📄 CLAIMS: {len(claims)} found")
        if claims:
            for claim in claims:
                print(f"   - {claim[1]} | {claim[2]} | KES {claim[3]:,.2f} | Status: {claim[4]}")
        else:
            print("   ⚠️ No claims found for this customer")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Main
if __name__ == "__main__":
    email = input("Enter customer email: ").strip()
    check_user_data(email)