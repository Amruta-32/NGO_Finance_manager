import os
from dotenv import load_dotenv
from supabase import create_client

# Force load .env file
load_dotenv(override=True)

# Get values
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"URL: {url}")
print(f"Key exists: {bool(key)}")

if not url or not key:
    print("❌ ERROR: SUPABASE_URL or SUPABASE_KEY not found!")
    print("Create a .env file with:")
    print("SUPABASE_URL=https://qadhpektxxvkucnqdqc.supabase.co")
    print("SUPABASE_KEY=your_key_here")
else:
    try:
        supabase = create_client(url, key)
        # Try a simple query
        result = supabase.table("ngos").select("*").limit(1).execute()
        print("✅ Connection successful!")
        print(f"Result: {result.data}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")