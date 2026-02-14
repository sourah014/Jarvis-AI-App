import google.generativeai as genai

# Yahan apni ASLI key paste karo (AIza wali)
MY_KEY = "AIzaSyBGhFxBrsFHdbd7ZrlIN1mIpXpb6_2Bung"  # <--- Yahan Key daalo

try:
    genai.configure(api_key=MY_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hi, are you working?")
    print("✅ SUCCESS! Jawab aaya:", response.text)
except Exception as e:
    print("❌ ERROR! Key kaam nahi kar rahi:", e)