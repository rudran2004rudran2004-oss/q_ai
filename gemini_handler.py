import os
import google.generativeai as genai

os.environ["GEMINI_API_KEY"] = "AIzaSyBu7755zXh5tKzxtM2OXnOuwU9iZAJMTRw"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

def chat(message):
    response = model.generate_content(message)
    return response.text

