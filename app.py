import streamlit as st
import requests
import json
import re
import PyPDF2

# --- Constants & Configuration ---
GENSARA_API_KEY = "gk_live_ATCc1WwXYVPKt2nkiM0_8ZzWBSG0LrGwPI6PmQyeJtA"
GENSARA_API_URL = "https://api.gensaralabs.com/api/chat"
PROMPTOS_ID = "0f28cd6c-fe6b-11f0-9b23-baae711029b4"

st.set_page_config(page_title="Resume Analyzer (TalentLens)", layout="wide", page_icon="📄")

# --- Helper Functions ---

def extract_text_from_pdf(pdf_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def clean_text(text):
    """Cleans extracted text by removing extra whitespace and special characters."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def analyze_candidate(resume_text, job_description):
    """
    Calls Gensara AI API to perform Skill Extraction, Analysis, 
    Candidate Scoring, and Report Generation simultaneously.
    """
    prompt = f"""
    You are an expert technical recruiter and HR analyst. Please act as an assistant to analyze a candidate's resume against a provided job description.
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME TEXT:
    {resume_text}
    
    Please provide the following in your analysis, structured clearly using Markdown formatting:
    
    ### 1. Skill Extraction
    List the key skills found in the resume. Next to each, clearly indicate if it matches the job description requirements.
    
    ### 2. Candidate Analysis
    Provide a paragraph analyzing the candidate's alignment with the role, highlighting their strengths and any missing crucial requirements.
    
    ### 3. Candidate Score
    Provide a specific score out of 100 based on how well the resume matches the job description, along with a 1-sentence justification for the score.
    
    ### 4. Final Recommendation & Report
    A concluding summary recommendation on whether to proceed with an interview, and 2-3 specific technical/behavioral questions to ask this candidate based on their background.
    """
    
    headers = {
        "Authorization": f"Bearer {GENSARA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": prompt,
        "promptos_id": PROMPTOS_ID,
        "temperature": 0.2  # Lower temp for more factual/analytical assessment
    }
    
    try:
        response = requests.post(GENSARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Process the response depending on typical API structures
        if "response" in data:
             return data["response"]
        elif "message" in data:
             return data["message"]
        elif "choices" in data:
             return data["choices"][0]["message"]["content"]
        elif "data" in data and isinstance(data["data"], str):
             return data["data"]
        else:
             return "I received a response from the API, but could not parse the format. Raw response:\n```json\n" + json.dumps(data, indent=2) + "\n```"
             
    except requests.exceptions.HTTPError as http_err:
        return f"**HTTP Error:** {http_err}\n\n**API Response Details:**\n```json\n{response.text}\n```"
    except Exception as e:
        return f"**Error parsing API response or connecting:** {e}"

# --- Main Streamlit UI ---

def main():
    st.title("TalentLens: AI-Powered Resume Analyzer 🎯")
    st.markdown("Automate your resume screening process using Gensara AI. Upload a resume, paste the job description, and instantly receive candidate scoring and analysis.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 1. Job Description")
        job_description = st.text_area("Paste the specific Job Description here:", height=300, 
                                       placeholder="e.g. Seeking a senior Python developer with experience in API development, AWS, and a strong problem-solving mindset...")
        
    with col2:
        st.subheader("📄 2. Candidate Resume")
        uploaded_file = st.file_uploader("Upload Resume (PDF format only)", type=["pdf"])
        
    st.divider()
    
    if st.button("🚀 Analyze Candidate Match", type="primary", use_container_width=True):
        if not job_description:
            st.warning("Please provide a job description to match against.")
            return
            
        if not uploaded_file:
            st.warning("Please upload a candidate resume document.")
            return
            
        with st.status("Processing Candidate Details...", expanded=True) as status:
            st.write("Extracting Text from PDF...")
            raw_text = extract_text_from_pdf(uploaded_file)
            
            if not raw_text:
                status.update(label="Failed to extract text from PDF.", state="error")
                return
                
            st.write("Cleaning and formatting Text...")
            cleaned_resume = clean_text(raw_text)
            
            st.write("Connecting to Gensara AI for comprehensive analysis (this may take a few seconds)...")
            report = analyze_candidate(cleaned_resume, job_description)
            
            status.update(label="Analysis Complete!", state="complete", expanded=False)
            
        st.header("📊 Evaluation Report")
        st.markdown(report)
        
        with st.expander("View Cleaned Resume Text (Hidden by default)"):
            st.text(cleaned_resume)

if __name__ == "__main__":
    main()
