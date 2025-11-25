"""
Deep diagnostic to find the real issue
"""

import sys
import os

print("=" * 70)
print("DEEP DIAGNOSTIC - FINDING THE REAL ISSUE")
print("=" * 70)

# 1. Python environment
print(f"\n1️⃣ Python Environment:")
print(f"   Version: {sys.version}")
print(f"   Executable: {sys.executable}")
print(f"   Platform: {sys.platform}")

# 2. Check all installed packages
print(f"\n2️⃣ Checking installed packages...")
import subprocess
result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                       capture_output=True, text=True)
packages = result.stdout

# Look for openai and related packages
print("\n   OpenAI-related packages:")
for line in packages.split('\n'):
    if 'openai' in line.lower() or 'httpx' in line.lower() or 'pydantic' in line.lower():
        print(f"   {line}")

# 3. Import and inspect openai
print(f"\n3️⃣ Importing openai module...")
try:
    import openai
    print(f"   ✅ Version: {openai.__version__}")
    print(f"   ✅ Location: {openai.__file__}")
    
    # Check the actual source code location
    import inspect
    from openai import AzureOpenAI
    
    print(f"\n4️⃣ Inspecting AzureOpenAI class...")
    print(f"   Class location: {inspect.getfile(AzureOpenAI)}")
    
    # Get the actual __init__ signature
    sig = inspect.signature(AzureOpenAI.__init__)
    print(f"\n   Parameters in AzureOpenAI.__init__:")
    for param_name, param in sig.parameters.items():
        default = param.default
        if default == inspect.Parameter.empty:
            default = "required"
        print(f"      • {param_name}: {default}")
    
    # Check if proxies exists
    params = list(sig.parameters.keys())
    if 'proxies' in params:
        print(f"\n   ⚠️ WARNING: 'proxies' found at position {params.index('proxies')}")
    
    # 5. Try to trace where proxies is coming from
    print(f"\n5️⃣ Checking parent class...")
    for base in AzureOpenAI.__mro__:
        print(f"   - {base}")
        if base != object and base != AzureOpenAI:
            try:
                base_sig = inspect.signature(base.__init__)
                if 'proxies' in base_sig.parameters:
                    print(f"     ⚠️ '{base.__name__}' has 'proxies' parameter!")
            except:
                pass
    
    # 6. Try creating with each parameter explicitly
    print(f"\n6️⃣ Testing parameter acceptance...")
    
    test_params = {
        'api_version': '2024-08-01-preview',
        'azure_endpoint': 'https://test.openai.azure.com/',
        'api_key': 'test_key'
    }
    
    for param, value in test_params.items():
        try:
            kwargs = {param: value}
            # Try just this one parameter
            print(f"   Testing with {param}={value[:30]}... ", end='')
            test = AzureOpenAI(**kwargs)
            print("❌ Shouldn't work with just this param")
        except TypeError as e:
            if 'proxies' in str(e):
                print(f"❌ PROXIES ERROR: {e}")
            else:
                print(f"✅ Expected error: {str(e)[:50]}")
        except Exception as e:
            print(f"✅ Different error: {type(e).__name__}")
    
    # 7. Try the actual creation
    print(f"\n7️⃣ Attempting actual client creation...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        client = AzureOpenAI(
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY')
        )
        print("   ✅ SUCCESS! Client created!")
        
    except TypeError as e:
        print(f"   ❌ TypeError: {e}")
        
        # Show the full traceback
        print("\n   Full traceback:")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"   ❌ Cannot import: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)