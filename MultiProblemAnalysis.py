import os
import json
import requests
from flask import Flask, request, render_template_string
import markdown as md

app = Flask(__name__)

# Register markdown filter for Jinja2
@app.template_filter('markdown')
def markdown_filter(text):
    return md.markdown(text)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SOLVER_PROMPT = """The goal is to determine which constraint programming solver would be best suited for this problem, considering the following options:\n\n- Gecode\n- Chuffed\n- Google OR-Tools CP-SAT\n- HiGHS\n- COIN-OR CBC\n\nPlease analyze the model and recommend the best solver for this problem, explaining your reasoning."""

# Load problems at startup
with open("mznc2025_probs/problems_with_descriptions.json", "r") as f:
    problems = json.load(f)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Gemini Multi-Problem Solver Recommendation</title></head>
<body>
    <h2>Choose a Problem for Gemini Solver Recommendation</h2>
    <form method="post">
        <label>Prompt Type:</label>
        <input type="radio" name="prompt_type" value="full" {% if prompt_type != 'name' %}checked{% endif %}> Full analysis & reasoning
        <input type="radio" name="prompt_type" value="name" {% if prompt_type == 'name' %}checked{% endif %}> Solver name only<br><br>
        {% for key, prob in problems.items() %}
            <button type="submit" name="problem" value="{{ key }}">{{ key }}</button><br>
        {% endfor %}
    </form>
    {% if response %}
        <hr>
        <h3>Gemini Response for <b>{{ selected_problem }}</b></h3>
        <div>{{ response | markdown | safe }}</div>
        <hr>
        <h4>Prompt sent to Gemini:</h4>
        <pre style="background:#f8f8f8; border:1px solid #ccc; padding:10px;">{{ prompt_text }}</pre>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    response_text = None
    selected_problem = None
    prompt_type = 'full'
    prompt_text = None
    if request.method == 'POST':
        selected_problem = request.form.get('problem')
        prompt_type = request.form.get('prompt_type', 'full')
        prob = problems[selected_problem]
        description = prob.get('description', '')
        script = prob.get('script', '')
        # If script is a path, read the file content
        if script.startswith('./'):
            script_path = script[2:] if script.startswith('./') else script
            try:
                with open(script_path, 'r') as sf:
                    script_content = sf.read()
                script = script_content
            except Exception as e:
                script = f"[Error reading {script_path}: {e}]"
        if prompt_type == 'name':
            solver_prompt = "The goal is to determine which constraint programming solver would be best suited for this problem, considering the following options:\n\n- Gecode\n- Chuffed\n- Google OR-Tools CP-SAT\n- HiGHS\n- COIN-OR CBC\n\nAnswer only with the name of the 3 best solvers, separated by comma and nothing else."
        else:
            solver_prompt = SOLVER_PROMPT
        prompt_text = f"Description:\n{description}\n\nMiniZinc model:\n{script}\n\n{solver_prompt}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text}
                    ]
                }
            ]
        }
        r = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, headers={'Content-Type': 'application/json'})
        data = r.json()
        response_text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', str(data))
    return render_template_string(HTML_TEMPLATE, problems=problems, response=response_text, selected_problem=selected_problem, prompt_type=prompt_type, prompt_text=prompt_text)

if __name__ == '__main__':
    app.run(debug=True)
