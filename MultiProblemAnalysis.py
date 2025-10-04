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
        <hr>
        <h3>Or enter a custom problem:</h3>
        <label>Description:</label><br>
        <textarea name="custom_description" rows="3" cols="80"></textarea><br>
        <label>MiniZinc model:</label><br>
        <textarea name="custom_model" rows="10" cols="80"></textarea><br>
        <button type="submit">Submit Custom Problem</button>
    </form>
    {% if response %}
        <hr>
        <h3>Gemini Response for <b>{{ selected_problem if selected_problem else 'Custom Problem' }}</b></h3>
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
        # Check if custom problem is submitted
        custom_description = request.form.get('custom_description', '').strip()
        custom_model = request.form.get('custom_model', '').strip()
        if custom_description and custom_model:
            description = custom_description
            script = custom_model
        else:
            prob = problems.get(selected_problem, {})
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
            solver_prompt = "The goal is to determine which constraint programming solver would be best suited for this problem, considering the following options:\n\n- Gecode\n- Chuffed\n- OR-Tools CP-SAT\n- HiGHS\n- COIN-BC\n\nAnswer only with the name of the 3 best solvers, separated by comma and nothing else."
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
        # Automatic check with top3_solvers from JSON
        if prompt_type == 'name' and selected_problem and selected_problem in problems:
            challenge_top3 = problems[selected_problem].get('top3_solvers', [])
            gemini_top3 = [s.strip() for s in response_text.split(',') if s.strip()]
            # Check for exact order match
            order_match = gemini_top3 == challenge_top3
            order_match_count = sum([g == c for g, c in zip(gemini_top3, challenge_top3)])
            # Count matches regardless of order
            unordered_match_count = len(set(gemini_top3) & set(challenge_top3))
            match_info = f"<b>MiniZinc Challenge Top 3:</b> {', '.join(challenge_top3)}<br>"
            match_info += f"<b>Gemini Top 3:</b> {', '.join(gemini_top3)}<br>"
            match_info += f"<b>Exact order matches:</b> {order_match_count} / 3<br>"
            match_info += f"<b>Unordered matches:</b> {unordered_match_count} / 3"
            if order_match:
                match_info += "<br><b>Order is correct!</b>"
            else:
                match_info += "<br><b>Order is NOT correct.</b>"
            response_text = match_info + "<hr>" + response_text
    return render_template_string(HTML_TEMPLATE, problems=problems, response=response_text, selected_problem=selected_problem, prompt_type=prompt_type, prompt_text=prompt_text)

if __name__ == '__main__':
    app.run(debug=True)
