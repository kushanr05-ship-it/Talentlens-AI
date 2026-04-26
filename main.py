from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import io
import csv
from fastapi.staticfiles import StaticFiles
import PyPDF2
import requests
import re
import os
from pydantic import BaseModel
from typing import List
from fastapi import Depends
from database import SessionLocal, Candidate
from sqlalchemy.orm import Session

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount the static directory to serve index.html, style.css, script.js
try:
    os.makedirs(STATIC_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
except Exception:
    # Vercel's serverless environment has a read-only filesystem and may crash here.
    pass

GENSARA_API_KEY = "gk_live_ATCc1WwXYVPKt2nkiM0_8ZzWBSG0LrGwPI6PmQyeJtA"
GENSARA_API_URL = "https://api.gensaralabs.com/api/chat"
PROMPTOS_ID = "0f28cd6c-fe6b-11f0-9b23-baae711029b4"

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/analyze")
async def analyze_resume(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if len(resumes) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 resumes allowed per evaluation.")
        
    extracted_texts = []
    filenames = []
    
    for r in resumes:
        if not r.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {r.filename} must be a PDF.")
            
        try:
            pdf_reader = PyPDF2.PdfReader(r.file)
            raw_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
                    
            cleaned_text = clean_text(raw_text)
            extracted_texts.append(cleaned_text)
            filenames.append(r.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading PDF {r.filename}: {str(e)}")
            
    combined_resumes = ""
    if len(resumes) == 1:
        combined_resumes = extracted_texts[0]
        prompt = f"""
        You are an expert technical recruiter and HR analyst. Please act as an assistant to analyze a candidate's resume against a provided job description.
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME TEXT:
        {combined_resumes}
        
        Please provide the following in your analysis, structured clearly using Markdown formatting. DO NOT wrap with ```markdown tags.
        
        ### 1. Skill Extraction
        List the key skills found in the resume. Next to each, clearly indicate if it matches the job description requirements.
        
        ### 2. Candidate Analysis
        Provide a paragraph analyzing the candidate's alignment with the role, highlighting their strengths and any missing crucial requirements.
        
        ### 3. Candidate Score
        Provide a specific score out of 100 based on how well the resume matches the job description, along with a 1-sentence justification for the score.
        
        ### 4. Final Recommendation & Report
        A concluding summary recommendation on whether to proceed with an interview, and 2-3 specific technical/behavioral questions to ask this candidate based on their background.
        """
    else:
        for i, text in enumerate(extracted_texts):
            combined_resumes += f"\n\n--- CANDIDATE {i+1}: {filenames[i]} ---\n{text}"
            
        prompt = f"""
        You are an expert Executive Technical Recruiter. You are provided with multiple candidate resumes and a Job Description.
        Rank the candidates from best fit to worst fit. Provide a clear Leaderboard.
        For each candidate, explain WHY they ranked where they did, their strengths, and missing requirements.
        Output MUST be in markdown format. DO NOT wrap with ```markdown tags.
        
        JOB DESCRIPTION:
        {job_description}
        
        CANDIDATES:
        {combined_resumes}
        """
        
    headers = {
        "Authorization": f"Bearer {GENSARA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": prompt,
        "promptos_id": PROMPTOS_ID,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(GENSARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        report = ""
        if "response" in data:
             report =  data["response"]
        elif "message" in data:
             report =  data["message"]
        elif "choices" in data:
             report =  data["choices"][0]["message"]["content"]
        elif "data" in data and isinstance(data["data"], str):
             report = data["data"]
        else:
             report = "Could not parse API format. Raw:\n```json\n" + str(data) + "\n```"
             
        # Save to SQLite Database
        db_candidate = Candidate(
            filename=", ".join(filenames),
            job_description=job_description,
            resume_text=combined_resumes,
            report=report
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
             
        return {"report": report, "resume_text": combined_resumes}
             
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gensara API Error: {str(e)}")

@app.get("/api/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return candidates

@app.get("/api/candidates/csv")
async def get_candidates_csv(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    # Write the CSV Header mappings
    writer.writerow(["ID", "Filename", "Evaluated At", "Missing Requirements / Strengths / AI Report Log"])
    
    for c in candidates:
         writer.writerow([c.id, c.filename, str(c.created_at), c.report])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=talentlens_history.csv"}
    )

@app.post("/api/upgrade")
async def upgrade_resume(
    job_description: str = Form(...),
    resume: UploadFile = File(...)
):
    if not resume.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        pdf_reader = PyPDF2.PdfReader(resume.file)
        raw_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")
        
    cleaned_resume = clean_text(raw_text)
    
    prompt = f"""
    You are an expert Executive Resume Writer and Career Coach. Rewrite the following candidate's resume summary and experience achievements to perfectly align with the target job description. Make them sound highly impactful and professional.
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME TEXT:
    {cleaned_resume}
    
    Provide the upgraded resume draft using clear Markdown formatting. Do not include introductory notes, just the optimized resume text.
    """
    
    headers = {
        "Authorization": f"Bearer {GENSARA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": prompt,
        "promptos_id": PROMPTOS_ID,
        "temperature": 0.5  # Slightly more creative for rewriting
    }
    
    try:
        response = requests.post(GENSARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        upgraded_text = ""
        if "response" in data:
             upgraded_text = data["response"]
        elif "message" in data:
             upgraded_text = data["message"]
        elif "choices" in data:
             upgraded_text = data["choices"][0]["message"]["content"]
        else:
             upgraded_text = "Analysis successful, but could not parse Gensara rewrite response."
             
        return {"report": upgraded_text}
             
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gensara API Error: {str(e)}")

class ChatRequest(BaseModel):
    resume_text: str
    question: str

@app.post("/api/chat")
async def chat_with_resume(request: ChatRequest):
    prompt = f"""
    You are an expert HR Assistant answering a recruiter's follow-up questions about a specific candidate's resume.
    Base your answer strictly on the provided resume text. If the resume doesn't contain the answer, say "The resume does not mention..."
    
    CANDIDATE RESUME:
    {request.resume_text}
    
    RECRUITER QUESTION:
    {request.question}
    
    Answer concisely and professionally.
    """
    
    headers = {
        "Authorization": f"Bearer {GENSARA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": prompt,
        "promptos_id": PROMPTOS_ID,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(GENSARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        answer = ""
        if "response" in data:
             answer = data["response"]
        elif "message" in data:
             answer = data["message"]
        elif "choices" in data:
             answer = data["choices"][0]["message"]["content"]
        else:
             answer = "I could not retrieve an answer from Gensara."
             
        return {"answer": answer}
             
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gensara Chat Error: {str(e)}")
