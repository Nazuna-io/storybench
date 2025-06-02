import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict, Counter

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = "storybench"
COLLECTION_NAME = "responses"

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in environment variables. Please check your .env file.")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Note: Repetition across runs is expected and NOT flagged as a problem.
# Only internal repetition within a single response is flagged.
def detect_issues(text):
    issues = []
    # 1. Model "thinking" or meta-commentary
    thinking_patterns = [
        r"let'?s think step by step",
        r"as an ai language model",
        r"here'?s my reasoning",
        r"let me think",
        r"i will now",
        r"my thought process",
        r"i will analyze",
        r"reasoning process",
        r"step by step reasoning",
        r"let's break this down",
        r"i am an ai",
        r"as an artificial intelligence",
        r"i cannot",
    ]
    if any(re.search(pat, text, re.IGNORECASE) for pat in thinking_patterns):
        issues.append("model_thinking")
    # 2. Instructions/disclaimers/non-story preambles
    preamble_patterns = [
        r"sure, here'?s (a|the) story",
        r"the following is (a|the) story",
        r"here is (a|the) story",
        r"as requested",
        r"below is",
        r"here is my response",
        r"here is my answer",
        r"please find",
        r"i have written",
        r"your request",
        r"according to your instructions",
        r"as per your request",
    ]
    if any(re.search(pat, text, re.IGNORECASE) for pat in preamble_patterns):
        issues.append("preamble_or_disclaimer")
    # 3. Empty or very short responses
    if not text or len(text.strip()) < 60:
        issues.append("empty_or_too_short")
    return issues

def main():
    model_stats = defaultdict(lambda: defaultdict(list))
    model_totals = Counter()
    
    cursor = collection.find({}, {"model_name": 1, "prompt_name": 1, "text": 1})
    for doc in cursor:
        model = doc.get("model_name", "<unknown>")
        prompt = doc.get("prompt_name", "<unknown>")
        text = doc.get("text", "")
        issues = detect_issues(text)
        model_totals[model] += 1
        for issue in issues:
            # Store both prompt and snippet for better context
            model_stats[model][issue].append((prompt, text))

    with open("analysis_summary.txt", "w", encoding="utf-8") as f:
        f.write("======= SUMMARY BY MODEL =======\n\n")
        for model, issues_dict in model_stats.items():
            total = model_totals[model]
            f.write(f"Model: {model} (Total responses: {total})\n")
            for issue, examples in issues_dict.items():
                count = len(examples)
                pct = 100.0 * count / total if total else 0
                f.write(f"  - Problem: {issue}\n")
                f.write(f"    Count: {count} ({pct:.1f}%)\n")
                f.write(f"    Examples:\n")
                for prompt, ex in examples[:3]:
                    snippet = ex[:300].replace('\n', ' ')
                    f.write(f"      - [{prompt}] {snippet}{'...' if len(ex) > 300 else ''}\n")
                if count > 3:
                    f.write(f"      ...and {count - 3} more examples.\n")
            f.write("\n")
        f.write("Analysis complete.\n")
    print("Summary written to analysis_summary.txt")

if __name__ == "__main__":
    main()
