import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key (first 10 chars): {api_key[:10] if api_key else 'NOT SET'}...")

try:
    genai.configure(api_key=api_key)
    
    # Try to list available models first
    print("\nAvailable models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
    
    # Try with different model names
    for model_name in ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro', 'gemini-2.0-flash']:
        try:
            print(f"\nTrying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say hello in one word")
            print(f"  SUCCESS: {response.text}")
            break
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {str(e)[:200]}")
            
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
