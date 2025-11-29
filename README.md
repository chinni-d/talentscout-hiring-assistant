# TalentScout — Hiring Assistant (Intern Assignment)

## Overview

A Streamlit-based Hiring Assistant that collects candidate info and generates tailored technical screening questions using an LLM. Built for the AI/ML intern assignment.

## Features

- Collects candidate details (Name, Email, Phone, Years, Desired position, Location, Tech stack).
- Generates 3–5 technical screening questions per technology listed.
- Maintains conversational context for follow-up questions.
- Simulated secure storage: submissions stored as encrypted JSON files (local).
- Exit keywords supported to gracefully end the conversation.

## Tech Stack

- Python, Streamlit
- OpenAI Chat API (or compatible LLM)
- cryptography (Fernet) for simulated encryption

## Installation

1. Clone repository.
2. Create a virtualenv and activate it.
3. Install dependencies:
