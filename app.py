"""
Streamlit Hiring Assistant (TalentScout) - main app
Run: streamlit run app.py
Environment variables:
  - OPENAI_API_KEY : Your OpenAI API key
  - ENCRYPTION_KEY : Optional (base64 urlsafe) for storing simulated encrypted submissions (Fernet)
"""

import streamlit as st
from llm_client import generate_questions_for_techstack, chat_followup
from utils import save_submission_encrypted, is_end_conversation, format_techstack
from prompts import INTAKE_PROMPT_BRIEF

st.set_page_config(page_title="TalentScout — Hiring Assistant", layout="centered")

EXIT_KEYWORDS = {"exit","quit","bye","end","stop","bye bye","thank you","thanks","done"}

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []  # list of (role, text)
if "candidate" not in st.session_state:
    st.session_state.candidate = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("TalentScout — Intelligent Hiring Assistant")
st.write("I will collect your details and generate technical screening questions based on your declared tech stack. Type 'exit' to end the conversation anytime.")

with st.expander("Instructions (brief)"):
    st.markdown("""
- Fill the candidate form and click **Start Screening**.  
- The assistant will generate 3–5 technical questions per technology you list.  
- You can chat / ask follow-up questions — context is maintained during the session.  
- Submissions are stored locally as simulated encrypted JSON (no external servers).
""")

# Candidate intake form
with st.form("candidate_form", clear_on_submit=False):
    st.subheader("Candidate Details")
    name = st.text_input("Full Name", value=st.session_state.candidate.get("name",""))
    email = st.text_input("Email", value=st.session_state.candidate.get("email",""))
    phone = st.text_input("Phone Number", value=st.session_state.candidate.get("phone",""))
    years = st.number_input("Years of Experience", min_value=0, max_value=60, value=st.session_state.candidate.get("years",0))
    desired = st.text_input("Desired Position(s)", value=st.session_state.candidate.get("desired",""))
    location = st.text_input("Current Location", value=st.session_state.candidate.get("location",""))
    techstack = st.text_area("Tech Stack (comma separated - languages, frameworks, DBs, tools)", value=st.session_state.candidate.get("techstack",""), height=80)
    submitted = st.form_submit_button("Start Screening")

if submitted:
    # basic validation
    if not name.strip() or not email.strip() or not techstack.strip():
        st.error("Please provide at least Name, Email and Tech Stack.")
    else:
        st.session_state.candidate = {
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "years": int(years),
            "desired": desired.strip(),
            "location": location.strip(),
            "techstack": techstack.strip()
        }
        st.session_state.submitted = True
        st.success("Candidate info captured. Generating tailored technical questions...")

# Main chat / output area
if st.session_state.submitted:
    # Display candidate summary
    st.markdown("### Candidate Summary")
    st.write(st.session_state.candidate)

    # Generate initial technical questions
    if "generated_questions" not in st.session_state:
        techs = format_techstack(st.session_state.candidate["techstack"])
        # call LLM to generate questions (returns dict: tech->list of questions)
        with st.spinner("Generating questions..."):
            qdict = generate_questions_for_techstack(techs,
                                                     candidate_info=st.session_state.candidate,
                                                     min_q=3, max_q=5)
        st.session_state.generated_questions = qdict
        # append to conversation for context
        st.session_state.conversation.append(("assistant", "Generated technical questions for the candidate."))

    # Show generated questions
    st.markdown("### Generated Technical Questions")
    for tech, qlist in st.session_state.generated_questions.items():
        st.markdown(f"**{tech}**")
        for i, q in enumerate(qlist, 1):
            st.write(f"{i}. {q}")

    # Chat interface for follow-up
    st.markdown("---")
    st.subheader("Chat / Follow-up (ask the assistant to rephrase, dig deeper, or request sample answers)")
    user_input = st.text_input("You:", key="chat_input")
    if st.button("Send", key="send_btn"):
        ui = user_input.strip()
        if ui == "":
            st.warning("Please type a message.")
        else:
            # Check for exit
            if is_end_conversation(ui):
                st.success("Conversation ended. Thank you! Candidate will be contacted with next steps.")
                st.session_state.conversation.append(("user", ui))
                st.session_state.conversation.append(("assistant", "Conversation ended. Thank you."))
                # Save simulated submission
                save_submission_encrypted(st.session_state.candidate, st.session_state.generated_questions)
                st.session_state.submitted = False
            else:
                st.session_state.conversation.append(("user", ui))
                # call follow-up LLM chat that uses context and returns a reply
                with st.spinner("Assistant is typing..."):
                    reply = chat_followup(ui, st.session_state.conversation, st.session_state.generated_questions)
                st.session_state.conversation.append(("assistant", reply))
    # show conversation
    st.markdown("### Conversation")
    for role, text in st.session_state.conversation[-12:]:
        if role == "user":
            st.markdown(f"**You:** {text}")
        else:
            st.markdown(f"**Assistant:** {text}")

# Footer / end
st.markdown("---")
st.caption("TalentScout — Intern Assignment implementation. Local storage used for demo only.")
