import pandas as pd
import requests
from dotenv import load_dotenv
import os
load_dotenv()

url = "https://jsearch.p.rapidapi.com/search?"

headers = {
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
    "x-rapidapi-key": os.getenv("x-rapidapi-key")
}

def get_cache_path(job_type, location, cache_dir="cache"):
    """
    Generate a file path for caching job results based on job type and location.
    """
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Use job type and location in the filename to avoid cache conflicts
    filename = f"{job_type}_{location.replace(' ', '_').replace(',', '')}.json"
    return os.path.join(cache_dir, filename)

# fetch recent jobs
def fetch_jobs(job_type, location, use_cache=True):
    cache_path = get_cache_path(job_type, location)

    if use_cache and os.path.exists(cache_path):
        # print(f"✅ Loaded cached jobs for: {job_type} in {location}")
        return pd.read_json(cache_path)

    # print(f"🌐 Fetching all job pages for: {job_type} in {location}")
    
    all_jobs = []
    batch = 1
    while True:
        params = {
            "query": f"{job_type} in {location}",
            "num_pages": "20",
            "page": str((batch - 1) * 20 + 1),  # e.g., 1, 21, 41, ...
            "date_posted": "week"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            results = response.json().get("data", [])
        except Exception as e:
            # print(f"⚠️ API error on batch {batch}: {e}")
            break

        if not results:
            break

        all_jobs.extend(results)
        batch += 1

    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df.to_json(cache_path, orient="records")

    return df

# extract job description and qualification info
def extract_job_info(df):
    # extract individual fields with fallbacks
    def get_desc(row):
        return row.get("job_description", "") or ""

    def get_quals(row):
        return " ".join(row.get("job_highlights", {}).get("Qualifications", [])) or ""

    def get_resp(row):
        return " ".join(row.get("job_highlights", {}).get("Responsibilities", [])) or ""

    def combine_fields(row):
        return " ".join([get_desc(row), get_quals(row), get_resp(row)])

    # create new columns
    df["job_description_text"] = df.apply(get_desc, axis=1)
    df["qualifications_text"] = df.apply(get_quals, axis=1)
    df["combined_text"] = df.apply(combine_fields, axis=1)
    return df