from sentence_transformers import SentenceTransformer
import torch
import pdfplumber
import torch.nn.functional as F
import base64
import io

# Initialize Sentence-BERT model (specifically fine-tuned for sentence similarity)
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_resume_text_from_base64(base64_string):
    """Decode base64-encoded string and extract text from PDF."""
    # Decode the base64 string
    pdf_data = base64.b64decode(base64_string.split(',')[1])

    # Use pdfplumber to extract text
    try:
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            text = ' '.join(page.extract_text() or '' for page in pdf.pages)
            if not text.strip():
                raise ValueError("No text found in resume PDF.")
            return text
    except Exception as e:
        print(f"Error reading resume: {e}")
        return ""  # Return empty string if an error occurs
    
# Function to get Sentence-BERT embeddings for a given text
def embed_text(text):
    return model.encode(text)

# Function to compute cosine similarity between resume and job description
def compute_similarity(resume_text, job_description):
    resume_embedding = embed_text(resume_text)
    job_embedding = embed_text(job_description)

    resume_tensor = torch.tensor(resume_embedding)
    job_tensor = torch.tensor(job_embedding)

    similarity = F.cosine_similarity(resume_tensor, job_tensor, dim=0)
    return similarity.item()

# Returns job matches based on resume
def get_matches(resume_text, jobs):
    matches = {}
    
    # Compute similarity for each job description
    for job_id in jobs.index:
        job_text = jobs.loc[job_id, "combined_text"]
        if not isinstance(job_text, str):
            # print(f"[WARNING] Job {job_id} has invalid combined_text of type {type(job_text)}")
            continue
        similarity_score = compute_similarity(resume_text, job_text)
        matches[job_id] = similarity_score

    return dict(sorted(matches.items(), key=lambda item: item[1], reverse=True))