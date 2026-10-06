import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "openai/gpt-oss-120b"

def get_client() -> OpenAI:
    """Initializes and returns the Groq client via OpenAI compatibility layer."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in the .env file.")
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )


def run_jd_analysis_agent(jd_text: str) -> dict:
    """
    Agent 1: Extracts structured criteria from the Job Description.
    """
    client = get_client()
    prompt = f"""
    You are an expert Talent Acquisition Specialist. Analyze the provided Job Description (JD) and extract key hiring requirements into structured JSON format.

    Return ONLY a JSON object with this exact structure:
    {{
      "role_title": "String - Job Title",
      "required_skills": ["List of mandatory technical and soft skills"],
      "preferred_skills": ["List of nice-to-have skills"],
      "experience_years": "String - e.g., '3-5 years' or 'Not specified'",
      "key_responsibilities": ["List of core job duties"]
    }}

    Job Description:
    {jd_text}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    return json.loads(response.choices[0].message.content)


def run_candidate_screening_agent(jd_analysis: dict, resume_text: str, candidate_name: str) -> dict:
    """
    Agent 2: Parses candidate resume against the extracted JD criteria to calculate match score and skill gaps.
    """
    client = get_client()
    prompt = f"""
    You are an AI Recruitment Analyst. Evaluate a candidate resume against the structured Job Requirements provided below.

    Job Requirements:
    {json.dumps(jd_analysis, indent=2)}

    Candidate Name: {candidate_name}
    Resume Text:
    {resume_text}

    Return ONLY a JSON object with this exact structure:
    {{
      "candidate_name": "{candidate_name}",
      "match_score": Integer between 0 and 100,
      "extracted_experience": "String - summary of key experience found",
      "matched_skills": ["List of skills candidate possesses that match JD"],
      "missing_skills": ["List of required/preferred skills candidate lacks"],
      "strengths": ["List of notable candidate strengths"],
      "gaps": ["List of identified experience/skill gaps"]
    }}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)


def run_interview_recommendation_agent(jd_analysis: dict, screening_result: dict) -> dict:
    """
    Agent 3: Synthesizes screening insights to generate custom interview questions and final hiring recommendation.
    """
    client = get_client()
    prompt = f"""
    You are a Senior Engineering/Product Manager conducting hiring decisions.
    Based on the Job Requirements and Candidate Screening Result below, generate tailormade interview questions and a final recommendation.

    Job Requirements:
    {json.dumps(jd_analysis, indent=2)}

    Screening Result:
    {json.dumps(screening_result, indent=2)}

    Return ONLY a JSON object with this exact structure:
    {{
      "recommendation": "Strong Shortlist" OR "Shortlist" OR "Reject",
      "justification": "Clear 2-3 sentence explanation for the hiring decision.",
      "interview_questions": [
        {{
          "category": "Technical Skill / Skill Gap / Experience Check",
          "question": "Targeted question to ask during interview",
          "intent": "Why this question should be asked"
        }}
      ]
    }}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    return json.loads(response.choices[0].message.content)