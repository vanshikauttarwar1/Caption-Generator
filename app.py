import os
import json
import random
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv  # <-- ADD THIS LINE

load_dotenv()  # <-- AND ADD THIS LINE

# --- Client Configuration for OpenRouter ---
# The rest of the code remains exactly the same.
# os.getenv("OPENROUTER_API_KEY") will now automatically find the key
# that load_dotenv() loaded from your .env file.
try:
    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.getenv("OPENROUTER_API_KEY"),
    )
except Exception as e:
    print("Error: Failed to initialize the OpenAI client.")
    print("Please ensure you have set the OPENROUTER_API_KEY in your .env file.")
    print(f"Details: {e}")
    exit()

app = Flask(__name__)

# Load few-shot examples from a JSON file
with open('examples.json', 'r') as f:
    FEW_SHOT_EXAMPLES = json.load(f)

def build_prompt(data):
    """
    Constructs the final prompt string with few-shot examples and constraints.
    """
    base_request = data.get('base_request', '')
    tone = data.get('tone', 'neutral')
    style = data.get('style', 'professional')
    content_format = data.get('content_format', 'text')
    keywords_str = data.get('keywords', '')
    char_limit_str = data.get('char_limit', '')

    # --- A/B Testing for Prompt Variations ---
    prompt_variation = random.choice(['A', 'B'])

    if prompt_variation == 'A':
        instruction = f"Generate content based on the following request: '{base_request}'."
    else:
        instruction = f"As a creative assistant, please compose content for this request: '{base_request}'."

    # --- Style and Tone ---
    style_instruction = f"The output must have a '{tone}' tone and a '{style}' style."

    # --- Few-Shot Examples ---
    examples_key = f"{content_format}_{style}"
    examples = FEW_SHOT_EXAMPLES.get(examples_key, [])
    few_shot_prompt = ""
    if examples:
        few_shot_prompt += "Here are some examples of the desired output:\n"
        for ex in examples:
            few_shot_prompt += f"Example:\n{ex}\n---\n"

    # --- Constraints ---
    constraints = []
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',')]
        constraints.append(f"It must include the following keywords: {', '.join(keywords)}.")
    if char_limit_str and char_limit_str.isdigit():
        constraints.append(f"The total length must not exceed {char_limit_str} characters.")

    constraint_instruction = " ".join(constraints)

    # --- Assemble the Final Prompt ---
    final_prompt = "\n".join(filter(None, [
        instruction,
        style_instruction,
        "Follow these rules:",
        constraint_instruction,
        few_shot_prompt,
        "Now, generate the content based on all the above instructions:"
    ]))

    return final_prompt, prompt_variation

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """
    The main endpoint to generate content.
    Receives user settings, builds a prompt, and returns the LLM response.
    """
    if not client.api_key:
        return jsonify({'error': 'OpenRouter API key is not configured. Please set the OPENROUTER_API_KEY environment variable.'}), 500

    data = request.json
    if not data or 'base_request' not in data:
        return jsonify({'error': 'Invalid request. "base_request" is required.'}), 400

    temperature = 0.7
    max_tokens = 50 # You can adjust this as needed

    try:
        final_prompt, prompt_variation = build_prompt(data)

        # --- Call the LLM API using the Chat Completions format for gpt-4o ---
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                # The system message helps set the behavior of the assistant.
                {"role": "system", "content": "You are an expert creative content generator. Follow the user's instructions precisely to control the tone, style, and constraints of the output."},
                # The user's message contains all the detailed instructions.
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        generated_text = response.choices[0].message.content.strip()

        # --- Return the result ---
        return jsonify({
            'generated_text': generated_text,
            'prompt_variation_used': prompt_variation,
            'full_prompt_sent': final_prompt
        })

    except Exception as e:
        # Provide more specific error feedback for API issues
        return jsonify({'error': f"An error occurred with the API call: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)