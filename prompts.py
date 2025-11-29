"""
Prompt templates and builder functions.
Design goals:
 - Be explicit about desired output format
 - Keep assistant constrained to screening purpose
 - Provide few-shot examples inline when helpful
"""

INTAKE_PROMPT_BRIEF = """
You are a hiring screening assistant for TalentScout.
Gather: Full Name, Email, Phone, Years of experience, Desired position(s), Location, and Tech Stack.
Then, ask the candidate to confirm their tech stack as comma-separated values.
Exit when candidate uses exit keywords: exit, quit, bye, stop.
"""

EXAMPLE_QS = """
Example format:
Python:
1. Explain the difference between lists and tuples in Python and when you would use each.
2. Write a function to reverse a string in-place and explain its time complexity.
3. Describe how Python's GIL affects multi-threaded CPU-bound programs.

Django:
1. Explain Django's request/response lifecycle.
2. How would you implement authentication for REST APIs in Django?
"""

def build_questions_prompt(tech_list, candidate_info=None, min_q=3, max_q=5):
    techs = ", ".join(tech_list)
    cand = ""
    if candidate_info:
        cand = f"Candidate: {candidate_info.get('name','')} | Experience: {candidate_info.get('years','')}, Desired: {candidate_info.get('desired','')}\n"
    prompt = f"""
You are an expert technical screener. Based on the candidate info below, generate {min_q} to {max_q} focused technical screening questions for each technology listed.
{cand}
Technologies: {techs}

OUTPUT FORMAT:
For each technology produce a header with the technology name followed by numbered questions, e.g.:

Python:
1. <question>
2. <question>
...

DIRECTIONS:
- Questions must be relevant to the technology and vary in difficulty (basic -> intermediate -> advanced).
- Do not ask irrelevant HR questions.
- Keep each question concise (one to two sentences).
- For libraries/frameworks, include at least one practical / coding style question and one architecture/design question if applicable.

{EXAMPLE_QS}
"""
    return prompt

def build_followup_prompt(user_message, conversation, generated_questions):
    # Provide short context: last assistant content + generated questions
    last_assistant = ""
    if conversation:
        for role, text in reversed(conversation):
            if role == "assistant":
                last_assistant = text
                break
    # include generated_questions summary
    summary_lines = []
    for tech, qlist in generated_questions.items():
        summary_lines.append(f"{tech}: {len(qlist)} questions")
    summary = "; ".join(summary_lines)
    prompt = f"""
User follow-up: "{user_message}"
Context summary: {summary}
Last assistant message: "{last_assistant}"

Instructions:
- Answer the user's query concisely related to technical screening or to the generated questions.
- If the user asks to modify or regenerate questions, follow the original constraints (3-5 questions per tech).
- If the user asks to end conversation, return a short confirmation like 'Conversation ended. Thank you.'
- If you cannot answer, reply with a helpful fallback message that asks for clarifying or offers alternatives but do not deviate from screening purpose.
"""
    return prompt
