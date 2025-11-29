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
    # Build comprehensive context
    conversation_context = ""
    if conversation:
        recent_exchanges = conversation[-6:]  # Last 3 exchanges (user + assistant pairs)
        for role, text in recent_exchanges:
            conversation_context += f"{role.capitalize()}: {text}\n"
    
    # Include the actual generated questions for context
    questions_context = ""
    for tech, qlist in generated_questions.items():
        questions_context += f"\n{tech} Questions:\n"
        for i, question in enumerate(qlist, 1):
            questions_context += f"  {i}. {question}\n"
    
    prompt = f"""
You are TalentScout's assistant helping with technical screening. 

CONVERSATION HISTORY:
{conversation_context}

GENERATED QUESTIONS:
{questions_context}

USER'S CURRENT MESSAGE: "{user_message}"

INSTRUCTIONS:
- Provide contextual help related to the screening process or the specific questions generated
- If asked to rephrase a question, provide a clearer version
- If asked to dig deeper, provide follow-up questions or explain the technical concept
- If asked for sample answers, provide brief example responses that a good candidate might give
- If asked to modify questions, suggest specific improvements
- Stay focused on technical screening and don't deviate to other topics
- Be concise but helpful (2-3 sentences maximum)

Respond directly to the user's request with relevant, actionable information.
"""
    return prompt
