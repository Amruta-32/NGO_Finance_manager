# NGO_Finance_manager 
A full-stack web application designed to digitally manage NGO operations such as beneficiary tracking, volunteer coordination, donation records , and transparent reporting.

🧪 How to Setup & Run (Environment Steps)

📥 1. Clone Project
git clone <your-repo-url>
cd ngo-management-system

🐍 2. Check Python Installed
python --version
👉 Must be Python 3.8+

📦 3. Create Virtual Environment
python -m venv venv

▶️ 4. Activate Environment
Windows:
venv\Scripts\activate
Mac/Linux:
source venv/bin/activate

📚 5. Install Dependencies
pip install -r requirements.txt

🔐 6. Setup Environment Variables
Create a file named .env in project root:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

🧠 7. Make sure code reads env (important)
import os
from supabase import create_client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

🚀 8. Run Project
python app.py
or if Flask:
flask run

🌐 9. Open in Browser
http://127.0.0.1:5000/

# Live Demo 
https://nurture-orphan.onrender.com/
