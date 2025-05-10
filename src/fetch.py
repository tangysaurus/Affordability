import pandas as pd
import asyncio
import aiohttp
from dotenv import load_dotenv
import os
load_dotenv()

async def fetch_jobs(session, url, headers, params):
    async with session.get(url, headers = headers, params = params) as response:
        try:
            data = await response.json()
            return data.get("data", [])
        except:
            return None

async def main(job_type, location):
    url = "https://jsearch.p.rapidapi.com/search?"

    headers = {
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("x-rapidapi-key")
    }
    try:
        async with aiohttp.ClientSession() as session:

            params_set = [{
                    "query": f"{job_type} in {location}",
                    "num_pages": "20",
                    "page": str((i - 1) * 20 + 1),
                    "date_posted": "week"
                } for i in range(1, 6)]

            tasks = [fetch_jobs(session, url, headers, params) for params in params_set]
            results = await asyncio.gather(*tasks)

            all_jobs = []

            for result in results:
                all_jobs.extend(result)

            return pd.DataFrame(all_jobs)
    finally:
        pass
            

# extract job description and qualification info
def extract_job_info(df):

    def get_quals(row):
        return " ".join(row.get("job_highlights", {}).get("Qualifications", [])) or ""

    def get_resp(row):
        return " ".join(row.get("job_highlights", {}).get("Responsibilities", [])) or ""

    def combine_fields(quals, resp):
        return " ".join([quals, resp]).strip()

    # Extract relevant fields
    df["id"] = df.apply(lambda row: row.get("job_id", ""), axis=1)
    df["title"] = df.apply(lambda row: row.get("job_title", ""), axis=1)
    df["employer"] = df.apply(lambda row: row.get("employer_name", ""), axis=1)
    df["apply_link"] = df.apply(lambda row: row.get("job_apply_link", ""), axis=1)
    df["description"] = df.apply(lambda row: row.get("job_description", ""), axis=1)
    df["qualifications"] = df.apply(get_quals, axis=1)
    df["responsibilities"] = df.apply(get_resp, axis=1)
    df["combined_text"] = df.apply(
        lambda row: combine_fields(row["qualifications"], row["responsibilities"]),
        axis=1
    )

    # extract relevant columns and set index to job id
    df = df[["id", "title", "employer", "apply_link", "description", "qualifications", "responsibilities", "combined_text"]]
    df.set_index("id", inplace = True)
    return df

# if __name__ == "__main__":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     df = asyncio.run(main("data scientist", "San Francisco"))
#     print(df)