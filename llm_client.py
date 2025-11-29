"""
LLM client wrapper using OpenAI Chat API (chat completions).
Replace with your LLM provider if needed.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import build_questions_prompt, build_followup_prompt

# Load environment variables from .env.local file
load_dotenv('.env.local')

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY is None:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable.")

# Initialize OpenAI client with OpenRouter endpoint
client = OpenAI(
    api_key=OPENAI_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def _call_chat(messages, temperature=0.2, max_tokens=800):
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",  # Free model on OpenRouter
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def generate_questions_for_techstack(tech_list, candidate_info=None, min_q=3, max_q=5):
    """
    tech_list: list of technology strings
    returns: dict mapping tech -> [questions...]
    """
    prompt = build_questions_prompt(tech_list, candidate_info=candidate_info, min_q=min_q, max_q=max_q)
    messages = [{"role":"system", "content":"You are a helpful technical screener for TalentScout."},
                {"role":"user", "content": prompt}]
    out = _call_chat(messages)
    # Expect structured output. We'll parse naive JSON-like structure from the assistant.
    # To keep robust, expect lines like "Tech: X\n1. ...\n2. ..."
    result = {}
    current = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith(":") and not line.startswith(("1.","2.","3.")):
            current = line[:-1]
            result[current] = []
        elif current and (line[0].isdigit() or line.startswith("-")):
            # strip leading "1. " or "- "
            cleaned = line.lstrip("0123456789. -")
            result[current].append(cleaned.strip())
        else:
            # fallback: if single tech, append lines
            if len(tech_list) == 1:
                t = tech_list[0]
                result.setdefault(t, []).append(line)
    # ensure min_q..max_q per tech
    for t in tech_list:
        qlist = result.get(t, [])
        if len(qlist) < min_q:
            qlist += [f"(Auto-generated fallback question {i+1} about {t})" for i in range(min_q-len(qlist))]
        result[t] = qlist[:max_q]
    return result

def chat_followup(user_message, conversation, generated_questions):
    """
    Uses conversation + generated_questions as context to answer follow-up user queries.
    """
    prompt = build_followup_prompt(user_message, conversation, generated_questions)
    messages = [{"role":"system","content":"You are TalentScout's assistant. Be concise, relevant, and do not deviate from screening purpose."},
                {"role":"user","content": prompt}]
    return _call_chat(messages, temperature=0.3, max_tokens=400)
