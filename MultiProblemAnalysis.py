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
        {% for key, prob in problems.items() %}
            <button type="submit" name="problem" value="{{ key }}">{{ key }}</button><br>
        {% endfor %}
    </form>
    {% if response %}
        <hr>
        <h3>Gemini Response for <b>{{ selected_problem }}</b></h3>
        <div>{{ response | markdown | safe }}</div>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    response_text = None
    selected_problem = None
    if request.method == 'POST':
        selected_problem = request.form.get('problem')
        prob = problems[selected_problem]
        description = prob.get('description', '')
        script = prob.get('script', '')
        prompt = f"Description:\n{description}\n\nMiniZinc model:\n{script}\n\n{SOLVER_PROMPT}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        r = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, headers={'Content-Type': 'application/json'})
        data = r.json()
        response_text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', str(data))
    return render_template_string(HTML_TEMPLATE, problems=problems, response=response_text, selected_problem=selected_problem)

if __name__ == '__main__':
    app.run(debug=True)
