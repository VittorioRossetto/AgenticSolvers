import os
import json
import requests

# ---------- Configuration ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ---------- Prompts ----------
SOLVER_PROMPT = """The goal is to determine which constraint programming solver would be best suited for this problem, considering the following options:

- Gecode
- Chuffed
- Google OR-Tools CP-SAT
- HiGHS
- COIN-OR CBC

Please analyze the model and recommend the best solver for this problem, explaining your reasoning."""

SOLVER_PROMPT_NAME_ONLY = """The goal is to determine which constraint programming solver would be best suited for this problem, considering the following options:

- Gecode
- Chuffed
- OR-Tools CP-SAT
- HiGHS
- COIN-BC

Answer only with the name of the 3 best solvers, separated by comma and nothing else."""

# ---------- Utility Functions ----------
def load_problems(json_path: str):
    with open(json_path, "r") as f:
        return json.load(f)

def get_problem_script(problem_entry: dict):
    """Reads the MiniZinc model content, even if it's a file path."""
    script = problem_entry.get('script', '')
    if script.startswith('./'):
        try:
            with open(script[2:], 'r') as sf:
                return sf.read()
        except Exception as e:
            return f"[Error reading {script}: {e}]"
    return script

def query_gemini(prompt_text: str):
    """Sends prompt to Gemini and returns the response text."""
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    data = response.json()
    return data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', str(data))

def evaluate_response(selected_problem: str, response_text: str, problems: dict):
    """Evaluates Gemini's response against the known top 3 solvers."""
    challenge_top3 = problems[selected_problem].get('top3_solvers', [])
    gemini_top3 = [s.strip() for s in response_text.split(',') if s.strip()]
    
    order_match = gemini_top3 == challenge_top3
    order_match_count = sum(g == c for g, c in zip(gemini_top3, challenge_top3))
    unordered_match_count = len(set(gemini_top3) & set(challenge_top3))
    
    match_info = (
        f"<b>MiniZinc Challenge Top 3:</b> {', '.join(challenge_top3)}<br>"
        f"<b>Gemini Top 3:</b> {', '.join(gemini_top3)}<br>"
        f"<b>Exact order matches:</b> {order_match_count} / 3<br>"
        f"<b>Unordered matches:</b> {unordered_match_count} / 3"
    )
    if order_match:
        match_info += "<br><b>Order is correct!</b>"
    else:
        match_info += "<br><b>Order is incorrect.</b>"
    
    return match_info