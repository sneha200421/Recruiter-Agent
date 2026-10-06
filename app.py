import streamlit as st
import pandas as pd
from parsers import extract_text_from_file
from agents import (
    run_jd_analysis_agent,
    run_candidate_screening_agent,
    run_interview_recommendation_agent,
)

# Page configuration
st.set_page_config(
    page_title="AI Recruitment Automation Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI Recruitment Automation Agent")
st.caption("Automated multi-agent candidate screening, skill gap analysis, and interview generation")

# Sidebar for Inputs
st.sidebar.header(" Workflow Inputs")

# 1. Job Description Input
st.sidebar.subheader("1. Job Description")
jd_file = st.sidebar.file_uploader("Upload JD (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
jd_text_input = st.sidebar.text_area("Or Paste JD Text directly:", height=150)

# 2. Resumes Upload
st.sidebar.subheader("2. Candidate Resumes")
resume_files = st.sidebar.file_uploader(
    "Upload Candidate Resumes (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

# Action Button
analyze_button = st.sidebar.button(" Analyze Candidates", use_container_width=True)

# Main Application Logic
if analyze_button:
    # Resolve Job Description Text
    final_jd_text = ""
    if jd_file:
        final_jd_text = extract_text_from_file(jd_file)
    elif jd_text_input.strip():
        final_jd_text = jd_text_input.strip()

    # Validations
    if not final_jd_text:
        st.error("Please upload or paste a Job Description before proceeding.")
        st.stop()

    if not resume_files:
        st.error("Please upload at least one candidate resume.")
        st.stop()

    # Step 1: Run JD Analysis Agent
    with st.spinner("Agent 1: Analyzing Job Description criteria..."):
        try:
            jd_analysis = run_jd_analysis_agent(final_jd_text)
            st.session_state["jd_analysis"] = jd_analysis
        except Exception as e:
            st.error(f"Failed to analyze Job Description: {str(e)}")
            st.stop()

    # Step 2 & 3: Run Candidate Screening & Recommendation Pipeline
    processed_candidates = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, r_file in enumerate(resume_files):
        cand_filename = r_file.name
        cand_name = cand_filename.rsplit(".", 1)[0].replace("_", " ").title()
        
        status_text.text(f"Processing candidate {idx + 1}/{len(resume_files)}: {cand_name}...")

        # Parse file
        cand_resume_text = extract_text_from_file(r_file)

        if cand_resume_text.startswith("[ERROR"):
            st.warning(f"Skipping {cand_filename} due to parsing error.")
            continue

        try:
            # Agent 2: Screening
            screening = run_candidate_screening_agent(jd_analysis, cand_resume_text, cand_name)
            
            # Agent 3: Interview Recommendation
            recommendation = run_interview_recommendation_agent(jd_analysis, screening)

            # Combine full evaluation result
            processed_candidates.append({
                "name": cand_name,
                "filename": cand_filename,
                "score": screening.get("match_score", 0),
                "decision": recommendation.get("recommendation", "N/A"),
                "screening": screening,
                "recommendation": recommendation,
            })
        except Exception as e:
            st.error(f"Error evaluating candidate {cand_name}: {str(e)}")

        # Update progress
        progress_bar.progress((idx + 1) / len(resume_files))

    status_text.empty()
    progress_bar.empty()

    # Sort candidates by match score descending
    processed_candidates.sort(key=lambda x: x["score"], reverse=True)
    st.session_state["candidates_results"] = processed_candidates


# --- DISPLAY RESULTS AREA ---
if "jd_analysis" in st.session_state and "candidates_results" in st.session_state:
    jd_info = st.session_state["jd_analysis"]
    results = st.session_state["candidates_results"]

    # Section 1: Job Criteria Summary
    st.header(" Target Role Analysis")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Role Title", jd_info.get("role_title", "Not Specified"))
    col_b.metric("Experience Req.", jd_info.get("experience_years", "Not Specified"))
    col_c.metric("Total Candidates Evaluated", len(results))

    with st.expander(" View Extracted JD Criteria Details"):
        st.write("**Required Skills:**", ", ".join(jd_info.get("required_skills", [])))
        st.write("**Preferred Skills:**", ", ".join(jd_info.get("preferred_skills", [])))
        st.write("**Key Responsibilities:**")
        for resp in jd_info.get("key_responsibilities", []):
            st.markdown(f"- {resp}")

    st.divider()

    # Section 2: Candidate Ranking Overview
    st.header(" Candidate Rankings")

    # Table View
    table_data = []
    for c in results:
        table_data.append({
            "Candidate": c["name"],
            "Match Score (%)": f"{c['score']}%",
            "Recommendation": c["decision"],
            "Matched Skills": len(c["screening"].get("matched_skills", [])),
            "Skill Gaps": len(c["screening"].get("missing_skills", [])),
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    st.divider()

    # Section 3: Deep-Dive Candidate Inspector
    st.header(" Detailed Candidate Insights")

    candidate_names = [c["name"] for c in results]
    selected_name = st.selectbox("Select Candidate to Inspect:", candidate_names)

    selected_cand = next((c for c in results if c["name"] == selected_name), None)

    if selected_cand:
        scr = selected_cand["screening"]
        rec = selected_cand["recommendation"]

        # Status badge & score
        col1, col2 = st.columns([1, 2])
        col1.metric(label="Match Score", value=f"{scr.get('match_score', 0)}%")
        
        rec_color = "🟢" if rec.get("recommendation") == "Strong Shortlist" else ("🟡" if rec.get("recommendation") == "Shortlist" else "🔴")
        col2.markdown(f"### Recommendation: {rec_color} `{rec.get('recommendation')}`")
        col2.write(f"**Justification:** {rec.get('justification')}")

        st.markdown("---")

        # Skills & Gaps Breakout
        c_left, c_right = st.columns(2)

        with c_left:
            st.subheader(" Matched Skills")
            for skill in scr.get("matched_skills", []):
                st.success(f"• {skill}")

            st.subheader(" Key Strengths")
            for strength in scr.get("strengths", []):
                st.markdown(f"- {strength}")

        with c_right:
            st.subheader(" Missing Skills / Gaps")
            for missing in scr.get("missing_skills", []):
                st.error(f"• {missing}")

            st.subheader(" Potential Risks")
            for gap in scr.get("gaps", []):
                st.markdown(f"- {gap}")

        st.markdown("---")

        # Custom Interview Questions
        st.subheader("AI-Generated Interview Questions")
        questions = rec.get("interview_questions", [])
        
        for q_idx, q in enumerate(questions, 1):
            with st.container():
                st.markdown(f"**Q{q_idx} [{q.get('category')}]**: {q.get('question')}")
                st.caption(f"*Assessment Goal:* {q.get('intent')}")
                st.write("")
else:
    st.info(" Please upload a Job Description and Candidate Resumes in the sidebar, then click 'Analyze Candidates'.")