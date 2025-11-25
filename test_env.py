import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Checking .env file...")
print(f"DB_SERVER: {os.getenv('DB_SERVER')}")
print(f"DB_DATABASE: {os.getenv('DB_DATABASE')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {'*' * len(os.getenv('DB_PASSWORD', ''))} ({len(os.getenv('DB_PASSWORD', ''))} characters)")

# Check for common issues
issues = []

if not os.getenv('DB_SERVER'):
    issues.append("❌ DB_SERVER is not set")
elif not os.getenv('DB_SERVER').endswith('.database.windows.net'):
    issues.append("⚠️ DB_SERVER should end with .database.windows.net")

if not os.getenv('DB_DATABASE'):
    issues.append("❌ DB_DATABASE is not set")

if not os.getenv('DB_USER'):
    issues.append("❌ DB_USER is not set")
elif '@' in os.getenv('DB_USER'):
    issues.append("⚠️ DB_USER should not contain @ symbol")

if not os.getenv('DB_PASSWORD'):
    issues.append("❌ DB_PASSWORD is not set")
elif len(os.getenv('DB_PASSWORD')) < 8:
    issues.append("⚠️ DB_PASSWORD seems too short")

if issues:
    print("\n⚠️ Found issues:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✅ All database environment variables look correct!")