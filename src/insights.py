import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from collections import defaultdict
from typing import List, Tuple
from fetch import fetch_jobs, extract_job_info
from tqdm import tqdm
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import logging
import json
import re
from dotenv import load_dotenv
import os
load_dotenv()

# --- Setup Logging ---
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# openai api key
key = os.getenv("openai-api-key")

# setup model
llm = ChatOpenAI(api_key = key, model="gpt-4-turbo", temperature=0)

# Prompt template
prompt = ChatPromptTemplate.from_template(
    "You're a career advisor. From the job description below, extract and categorize the 5–10 most important items into these three buckets:\n\n"
    "- Technical Skills\n- Soft Skills\n- Experience / Education\n\n"
    "Job Description:\n\n{job_description}\n\n"
    "Return a JSON object in this exact format:\n"
    "{{\n"
    "  \"technical_skills\": [\"...\"],\n"
    "  \"soft_skills\": [\"...\"],\n"
    "  \"experience_education\": [\"...\"]\n"
    "}}\n"
)

skill_extraction_chain = prompt | llm

# --- Caching ---
skill_cache = {}

def clean_json_response(content: str) -> str:
    """Extract JSON from raw content, regardless of format."""
    # Look for code block
    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        return match.group(1)

    # Look for bare JSON fallback
    match = re.search(r"(\{.*\})", content, re.DOTALL)
    if match:
        return match.group(1)

    return content.strip()

def get_skills_from_llm(description: str) -> dict:
    """Query LLM for categorized skills."""
    if description in skill_cache:
        return skill_cache[description]
    try:
        result = skill_extraction_chain.invoke({"job_description": description})
        content = result.content.strip()
        # logging.debug(f"Raw LLM output: {content}")

        cleaned = clean_json_response(content)
        parsed = json.loads(cleaned)

        skill_cache[description] = parsed
        return parsed
    # except json.JSONDecodeError as e:
    #     logging.warning(f"❌ JSON decode failed: {e}")
    #     logging.warning(f"Raw output was:\n{content}")
    # except Exception as e:
    #     logging.warning(f"Failed to extract skills: {e}")
    except:
        return {
            "technical_skills": [],
            "soft_skills": [],
            "experience_education": []
        }

def get_skills_in_parallel(descriptions: List[str], max_workers: int = 10) -> List[dict]:
    """Parallelized skill extraction with progress bar."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(get_skills_from_llm, descriptions), total=len(descriptions), desc="🔍 Extracting skills"))
    return results

def cluster_and_summarize(skills, top_n=5, eps=0.35):
    if not skills:
        return []

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(skills)
    clustering = DBSCAN(eps=eps, min_samples=1, metric="cosine").fit(embeddings)
    labels = clustering.labels_

    cluster_map = defaultdict(list)
    for label, skill in zip(labels, skills):
        cluster_map[label].append(skill)

    summarized = []
    for group in cluster_map.values():
        rep = min(group, key=len)
        summarized.append((rep, len(group)))
    return sorted(summarized, key=lambda x: x[1], reverse=True)[:top_n]

def get_top_keywords_semantic(categorized_skills: List[dict], top_n: int = 5) -> dict:
    """Aggregate top skills in each category using semantic deduplication."""
    buckets = ["technical_skills", "soft_skills", "experience_education"]
    output = {}

    for bucket in buckets:
        # Flatten all items in this bucket across jobs
        raw_skills = [s for d in categorized_skills for s in d.get(bucket, [])]
        # norm_skills = normalize_skills(raw_skills)
        top_skills = cluster_and_summarize(raw_skills, top_n=top_n)
        output[bucket] = top_skills

    return output

def get_job_insights(job_type: str, location: str, save_csv: bool = False) -> Tuple[pd.DataFrame, dict]:
    """Main function: fetch jobs, extract categorized skills, and return top insights."""
    # logging.info(f"📥 Fetching jobs for '{job_type}' in '{location}'...")
    df = fetch_jobs(job_type, location)
    if df.empty:
        # logging.warning("⚠️ No jobs found.")
        return pd.DataFrame(), {}

    df = extract_job_info(df)

    # logging.info("🔍 Extracting categorized skills from job descriptions...")
    df["extracted_skills"] = get_skills_in_parallel(df["combined_text"].tolist())

    # Parse JSON skill outputs
    categorized_skills = []
    for raw in df["extracted_skills"]:
        try:
            categorized_skills.append(raw)
        except Exception as e:
            # logging.warning(f"⚠️ Failed to parse skill JSON: {e}")
            categorized_skills.append({
                "technical_skills": [],
                "soft_skills": [],
                "experience_education": []
            })

    # logging.info("📊 Aggregating top skills with semantic clustering...")
    top_keywords = get_top_keywords_semantic(categorized_skills)

    # logging.info(f"✅ Found {len(df)} jobs posted in the past week.")
    # for bucket, skills in top_keywords.items():
    #     logging.info(f"\n🔥 Top {bucket.replace('_', ' ').title()}:")
    #     for skill, count in skills:
    #         logging.info(f"  {skill}: {count}")

    # if save_csv:
    #     filename = f"{job_type.replace(' ', '_')}_{location.replace(' ', '_')}_skills.csv"
    #     df.to_csv(filename, index=False)
        # logging.info(f"📁 Results saved to {filename}")

    return df, top_keywords