from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, request, render_template, jsonify
from markupsafe import escape
from openai import OpenAI
import re
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI client (OpenRouter)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.form.get("user_input", "").strip()
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    user_input = escape(user_input)

    if not user_input or len(user_input) < 3:
        return jsonify({"response": "Please enter a valid medical issue (at least 3 characters)."})

    location_info = ""
    if latitude and longitude:
        location_info = f"The user's location is: latitude {latitude}, longitude {longitude}. "

    prompt = (
        location_info +
        f"The user has the following medical issue: {user_input}. "
        "Provide 10 concise and clear first aid points for this issue in a numbered list format. "
        "Use simple language and ensure the information is specific to India. For example, use '108' for ambulance and '100' for police. "
        "Highlight important words in bold."
    )

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Medical First Aid Chatbot",
            },
            model="deepseek/deepseek-r1-distill-llama-8b",
            messages=[{"role": "user", "content": prompt}]
        )
        response = completion.choices[0].message.content
        formatted_response = format_response(response)
        return jsonify({"response": formatted_response})
    except Exception as e:
        logging.error(f"Error in get_response: {e}")
        return jsonify({"response": "An error occurred. Please try again later."})

def format_response(response):
    lines = response.split("\n")
    formatted_lines = []
    for line in lines:
        if line.strip() and not line.strip().startswith(("Note:", "Disclaimer:", "Warning:")):
            line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            formatted_lines.append(escape(line.strip()))
    return "\n".join(formatted_lines)

if __name__ == "__main__":
    app.run(debug=True)
