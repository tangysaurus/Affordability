from dotenv import load_dotenv
import os
import openai

# openai api key
load_dotenv()
openai.api_key = os.getenv("openai-api-key")

def get_feedback(resume_text, job_title, job_description):
    # setup model
    prompt = f"""
    You are a career expert and a recruiter assistant.

    I've uploaded my resume, and I want you to evaluate how well I fit the job based on the job description and the resume's content.

    Here is the job description:
    Job Title: {job_title}
    Job Description: {job_description}

    Here is my resume:
    Resume: {resume_text}

    Please answer the following and respond *strictly* in valid JSON, formatted exactly as follows:
    {{
    "How well does this resume match the job description?": ["<bullet point 1>", "<bullet point 2>", "..."],
    "Highlight key skills, experiences, or qualifications in the resume that make me a good fit for this job.": ["<bullet point 1>", "<bullet point 2>", "..."],
    "Point out any potential gaps or areas where I might need to improve to increase my chances for this role.": ["<bullet point 1>", "<bullet point 2>", "..."],
    "Overall, would you recommend I apply for this job? Why or why not?": ["<bullet point 1>", "<bullet point 2>", "..."]
    }}

    Provide comprehensive bullet points for each question, giving context around why this job would be a good or bad fit for me, based on the provided details.
    Do not include any introduction or markdown-respond with only valid JSON.
    """

    return get_response(prompt)

def get_insights(job_title, job_description):
    prompt = f"""
    You are an expert career coach. Analyze the following job description and respond *strictly* in valid JSON, formatted exactly as follows:

    {{
    "main_responsibilities": ["<bullet point 1>", "<bullet point 2>", "..."],
    "preferred_qualifications": ["<qualification 1>", "<qualification 2>", "..."],
    "key_skills": ["<skill 1>", "<skill 2>", "..."],
    "time_commitment_deadlines": ["<job type or time commitment>", "<date or timeframe>", "..."],
    "salary_benefits": ["<salary>", "<benefit 1>", "<benefit 2>", "..."],
    "automation_risk": "<one-line summary about automation or AI risk>"
    }}

    Use only short bullet points in lists. Do not include any introduction, summary, explanation, or markdown — respond with only valid JSON.

    ---
    Job Title: {job_title}
    Job Description: {job_description}
    """
    
    return get_response(prompt)

def get_response(prompt):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

