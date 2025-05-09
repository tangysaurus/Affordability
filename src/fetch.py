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

# fetch recent jobs
def fetch_jobs(job_type, location):
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
            break

        if not results:
            break

        all_jobs.extend(results)
        batch += 1

    df = pd.DataFrame(all_jobs)
    return df

# extract job description and qualification info
def extract_job_info(df):
    def get_id(row):
        return row.get("job_id", "")
    
    def get_title(row):
        return row.get("job_title", "") or ""
    
    def get_employer(row):
        return row.get("employer_name", "") or ""
    
    def get_employment_type(row):
        return row.get("job_employment_type_text", "") or ""
    
    def get_link(row):
        return row.get("job_apply_link", "") or ""

    def get_desc(row):
        return row.get("job_description", "") or ""

    def get_quals(row):
        return " ".join(row.get("job_highlights", {}).get("Qualifications", [])) or ""

    def get_resp(row):
        return " ".join(row.get("job_highlights", {}).get("Responsibilities", [])) or ""

    def combine_fields(quals, resp):
        return " ".join([quals, resp]).strip()

    # Extract relevant fields
    df["id"] = df.apply(get_id, axis=1)
    df["title"] = df.apply(get_title, axis=1)
    df["employer"] = df.apply(get_employer, axis=1)
    df["employment_type"] = df.apply(get_employment_type, axis=1)
    df["apply_link"] = df.apply(get_link, axis=1)
    df["description"] = df.apply(get_desc, axis=1)
    df["qualifications"] = df.apply(get_quals, axis=1)
    df["responsibilities"] = df.apply(get_resp, axis=1)
    df["combined_text"] = df.apply(
        lambda row: combine_fields(row["qualifications"], row["responsibilities"]),
        axis=1
    )
    # extract relevant columns and set index to job id
    df = df[["id", "title", "employer", "employment_type", "apply_link", "description", "qualifications", "responsibilities", "combined_text"]]
    df.set_index("id", inplace = True)
    return df