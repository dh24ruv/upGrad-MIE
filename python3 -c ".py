python3 -c "
from google import genai
import os
from dotenv import load_dotenv
load_dotenv('/Users/dhruvpande/upgrad/.env')
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
for m in client.models.list():
    print(m.name)
"