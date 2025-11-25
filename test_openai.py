"""
Azure OpenAI Connection Test
Tests connection to Azure OpenAI GPT-4o-mini deployment
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🤖 Testing Azure OpenAI connection...")
print("=" * 60)

# Step 1: Check OpenAI library version
try:
    import openai
    print(f"📦 OpenAI library version: {openai.__version__}")
    
    if openai.__version__.startswith("0."):
        print("❌ You have an OLD version of openai library!")
        print("   Please upgrade:")
        print("   pip install --upgrade openai")
        exit(1)
    else:
        print("✅ OpenAI library version is compatible")
except Exception as e:
    print(f"❌ Cannot import openai: {e}")
    print("   Install with: pip install openai")
    exit(1)

# Step 2: Get environment variables
print("\n📋 Loading configuration...")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

print(f"   Endpoint: {endpoint}")
print(f"   Deployment: {deployment}")
print(f"   API Version: {api_version}")
print(f"   API Key: {'*' * 20 if api_key else 'NOT SET'}")

# Step 3: Validate configuration
print("\n🔍 Validating configuration...")
errors = []

if not endpoint:
    errors.append("AZURE_OPENAI_ENDPOINT not set in .env")
if not api_key:
    errors.append("AZURE_OPENAI_API_KEY not set in .env")
if not deployment:
    errors.append("AZURE_OPENAI_DEPLOYMENT_NAME not set in .env")

if errors:
    print("❌ Configuration errors found:")
    for error in errors:
        print(f"   • {error}")
    exit(1)
else:
    print("✅ Configuration looks good")

# Step 4: Initialize Azure OpenAI client
print("\n🔌 Initializing Azure OpenAI client...")
try:
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )
    print("✅ Client initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Step 5: Test API call
print("\n🧪 Testing chat completion...")
try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for Hakikisha Insurance."
            },
            {
                "role": "user",
                "content": "Say 'Hello from Hakikisha Insurance!' if you can hear me."
            }
        ],
        max_tokens=50,
        temperature=0.7
    )
    
    reply = response.choices[0].message.content
    
    print("✅ API call successful!")
    print(f"\n💬 AI Response:")
    print(f"   {reply}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("   Your Azure OpenAI connection is working correctly.")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ API call failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Check deployment name in Azure Portal")
    print("   2. Verify API key is correct")
    print("   3. Ensure deployment is active")
    print("   4. Check for any Azure service outages")
    exit(1)