from groq import Groq
import json
import os
import time

# -------------------------------------------
# CONFIG
# -------------------------------------------
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
MODEL = "openai/gpt-oss-120b"   # Same as your earlier Groq judge model

client = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------

JUDGE_PROMPT = """
You are an automated evaluator. Your role is to assess the AI assistant’s final answer.

DO NOT judge formatting, grammar, or units. Small differences in wording, rounding,
or equivalent reasoning should NOT reduce the score.

Inputs:

- User Query
- Assistant Response
- Ground Truth Answer

Evaluate only the final response.

Scoring:

Helpfulness (0–10):
- Fully answers the question clearly → 8–10
- Partially useful or somewhat relevant → 5–7
- Slightly relevant but not useful → 3–4
- Mostly unhelpful → 1–2
- If the assistant asks for clarification instead of answering → -1

Accuracy (0 or 10 only):
- If the final answer meaningfully aligns with the ground truth in content, reasoning, or conclusion → 10
  (Exact matching is NOT required. Partial reasoning or alternate phrasing is acceptable if the core answer is correct.)
- If the answer is entirely incorrect, contradictory to the ground truth, or irrelevant → 0
- If the assistant asks for clarification instead of answering → -1

Output JSON format:

{
  "helpfulness": <number>,
  "accuracy": <number>,
  "analysis": "<short explanation>"
}
"""


# -------------------------------------------
# EVALUATION FUNCTION (SYNC)
# -------------------------------------------

def evaluate_response(item):
    messages = [
        {"role": "system", "content": JUDGE_PROMPT},
        {
            "role": "user",
            "content": json.dumps({
                "query": item["query"],
                "assistant_response": item["answer"],
                "ground_truth": item["ground_truth"]
            }, indent=2)
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0
        )

        result_text = response.choices[0].message.content.strip()

        try:
            return json.loads(result_text)

        except json.JSONDecodeError:
            return {
                "helpfulness": -1,
                "accuracy": -1,
                "analysis": f"Invalid JSON returned: {result_text}"
            }

    except Exception as e:
        return {
            "helpfulness": -1,
            "accuracy": -1,
            "analysis": f"API error: {str(e)}"
        }


# -------------------------------------------
# MAIN EXECUTION LOOP
# -------------------------------------------

def main():
    with open("dataset.json", "r") as f:
        dataset = json.load(f)

    print(dataset[0])

    results = []
    helpfulness_total = 0
    accuracy_total = 0
    count = 0

    for item in dataset:
        print(item)
        result = evaluate_response(item)
        results.append(result)
        print(result)

        if result.get("helpfulness") != -1:
            count += 1
            helpfulness_total += result["helpfulness"]
            accuracy_total += result["accuracy"]

        time.sleep(0.2)  # pacing delay (optional)

    if count > 0:
        print(f"ACCURACY: {accuracy_total / count}")
        print(f"HELPFULNESS: {helpfulness_total / count}")
    else:
        print("No valid scores returned.")


# -------------------------------------------
# ENTRY
# -------------------------------------------

if __name__ == "__main__":
    main()
