# test_kb_query.py

# Import everything needed from app.py
# NOTE: You will need to import all dependencies like os, load_dotenv, pyodbc, etc.
from app import query_knowledge_base, load_dotenv

# Ensure environment variables are loaded for DB connection
load_dotenv()

def run_test():
    print("\n--- Testing Knowledge Base Query (No Match) ---")

    # Test 3 (No Match/General Query)
    test_query = "your mpesa paybill number"
    print(f"Querying: {test_query}")

    results = query_knowledge_base(test_query)

    if not results:
        print("✅ TEST PASSED: Results list is empty.")
    else:
        print(f"❌ TEST FAILED: Unexpected results were returned: {results}")

if __name__ == "__main__":
    run_test()