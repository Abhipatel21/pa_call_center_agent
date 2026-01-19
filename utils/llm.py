from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

def get_llm():
    """
    Returns a configured ChatOpenAI instance.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment")
        
    return ChatOpenAI(
        model="gpt-4o", 
        temperature=0,
        streaming=True
    )
