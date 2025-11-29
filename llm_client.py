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
    messages = [{"role":"system", "content":"You are a helpful technical screener for TalentScout. ALWAYS format your response with technology names followed by numbered questions."},
                {"role":"user", "content": prompt}]
    
    try:
        out = _call_chat(messages)
    except Exception as e:
        print(f"Error calling LLM: {e}")
        # Return fallback questions if LLM fails
        result = {}
        for t in tech_list:
            result[t] = [f"Explain the core concepts of {t} and its main use cases.",
                        f"What are some best practices when working with {t}?",
                        f"Describe a challenging problem you've solved using {t}."][:max_q]
        return result
    
    # Improved parsing - more flexible approach
    result = {}
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    current_tech = None
    
    # First pass: identify technology sections
    for line in lines:
        # Check if this line contains a technology name
        for tech in tech_list:
            if tech.lower() in line.lower() and not line[0].isdigit():
                current_tech = tech
                if current_tech not in result:
                    result[current_tech] = []
                break
    
    # Second pass: extract questions
    current_tech = None
    for line in lines:
        # Check for tech headers again
        tech_found = False
        for tech in tech_list:
            if tech.lower() in line.lower() and not line[0].isdigit():
                current_tech = tech
                tech_found = True
                break
        
        if tech_found:
            continue
            
        # Check for questions (numbered, bulleted, or just substantial content)
        if current_tech and (line[0].isdigit() or line.startswith(("-", "*", "•", "Q", "q")) or len(line) > 15):
            # Clean the question
            question = line
            # Remove common prefixes
            prefixes_to_remove = ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.',
                                '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)', '10)',
                                '-', '*', '•', 'Q:', 'Question:']
            
            for prefix in prefixes_to_remove:
                if question.startswith(prefix):
                    question = question[len(prefix):].strip()
                    break
            
            if question and len(question) > 10:  # Only add substantial questions
                result[current_tech].append(question)
    
    # Fallback: if no proper parsing worked, split content evenly
    if not any(result.values()):
        # Try to extract any meaningful content and distribute
        meaningful_lines = [line for line in lines if len(line) > 20 and '?' in line]
        if meaningful_lines:
            questions_per_tech = len(meaningful_lines) // len(tech_list)
            for i, tech in enumerate(tech_list):
                start_idx = i * questions_per_tech
                end_idx = start_idx + questions_per_tech if i < len(tech_list) - 1 else len(meaningful_lines)
                result[tech] = meaningful_lines[start_idx:end_idx]
    
    # Ensure minimum questions for each tech
    for t in tech_list:
        qlist = result.get(t, [])
        if len(qlist) < min_q:
            # Add generic but relevant fallback questions
            fallbacks = [
                f"What are the key features and advantages of {t}?",
                f"Describe your experience working with {t} in professional projects.",
                f"What are common challenges developers face with {t} and how do you solve them?",
                f"How does {t} compare to similar technologies you've used?",
                f"What best practices do you follow when developing with {t}?"
            ]
            needed = min_q - len(qlist)
            qlist.extend(fallbacks[:needed])
        result[t] = qlist[:max_q]
    
    return result

def chat_followup(user_message, conversation, generated_questions):
    """
    Uses conversation + generated_questions as context to answer follow-up user queries.
    """
    prompt = build_followup_prompt(user_message, conversation, generated_questions)
    messages = [{"role":"system","content":"You are TalentScout's technical screening assistant. You help with questions about the screening process, can rephrase questions for clarity, provide sample answers, explain technical concepts, and assist with the hiring process. Always stay focused on technical screening and provide contextual, helpful responses."},
                {"role":"user","content": prompt}]
    return _call_chat(messages, temperature=0.3, max_tokens=600)
