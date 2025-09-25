# AgenticSolvers
The idea of this research is based on a novel paradigm for solving complex, NP-hard problems (e.g., schedul- ing, routing) by leveraging Large Language Models (LLMs) as dynamic orchestrators in Agentic solvers, as proposed in a position Paper by professor Roberto Amadini and Simone Gazza.

## MultiProblemAnalysis Flask App

This app provides an interface to get solver recommendations for various MiniZinc problems using the Gemini LLM.

### How it works
- Loads a set of MiniZinc problems and their descriptions from `mznc2025_probs/problems_with_descriptions.json`.
- For each problem, the app displays a button to request a solver recommendation.
- When a problem is selected, the app sends its description and MiniZinc model code to Gemini, asking for the best solver(s) and optionally a reasoning.
- The response from Gemini is shown in the browser, along with the prompt that was sent.
- You can choose between a detailed analysis or just the top 3 solver names.

### How to use
1. Make sure you have Python and Flask installed.
2. Set your Gemini API key in the environment variable `GEMINI_API_KEY`.
3. Run the app:
   ```bash
   python MultiProblemAnalysis.py
   ```
4. Open your browser and go to `http://127.0.0.1:5000/`.
5. Select a problem and prompt type, then view Gemini's recommendation and reasoning.
