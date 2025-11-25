print("Testing OpenAI import...")

try:
    import openai
    print(f"✅ OpenAI version: {openai.__version__}")
    print(f"✅ Location: {openai.__file__}")
    
    from openai import AzureOpenAI
    print("✅ AzureOpenAI imported successfully")
    
    # Check the signature of AzureOpenAI.__init__
    import inspect
    sig = inspect.signature(AzureOpenAI.__init__)
    print(f"\n📋 AzureOpenAI.__init__ parameters:")
    for param_name, param in sig.parameters.items():
        if param_name != 'self':
            print(f"   - {param_name}")
    
    # Check if 'proxies' is in parameters (it shouldn't be)
    if 'proxies' in sig.parameters:
        print("\n⚠️ WARNING: 'proxies' parameter found (shouldn't be there)")
    else:
        print("\n✅ No 'proxies' parameter (correct)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()