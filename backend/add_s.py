import os
import pdfplumber
import docx
import google.generativeai as genai

# -------------------------
# CONFIGURE GEMINI
# -------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # set this in your environment
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------
# Extract PDF text
# -------------------------
def extract_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
    return text

# -------------------------
# Extract DOCX text
# -------------------------
def extract_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

# -------------------------
# MAIN PROGRAM
# -------------------------
def main():
    print("🚀 AI Resume Scanner using Gemini\n")

    file_path = "resume.pdf"

    print("\nPaste Job Description (press ENTER twice to finish):")
    jd_lines = []
    while True:
        line = input()
        if line == "":
            break
        jd_lines.append(line)

    job_desc = " ".join(jd_lines)

    # Extract resume text
    if file_path.endswith(".pdf"):
        resume_text = extract_pdf(file_path)
    elif file_path.endswith(".docx"):
        resume_text = extract_docx(file_path)
    else:
        print("❌ Unsupported file format")
        return

    # -------------------------
    # AI PROMPT
    # -------------------------
    prompt = f"""
    You are an AI Resume Screening System.

    Analyze the resume against the job description and provide:

    1. Match Score (0-100)
    2. Key Skills Found
    3. Missing Skills
    4. Experience Level
    5. Strengths
    6. Weaknesses
    7. Suggestions for Improvement
    8. Dont use any formatting like markdown or html, just plain text with clear labels.

    Resume:
    {resume_text}

    Job Description:
    {job_desc}

    Give output in a clean structured format.
    """

    # -------------------------
    # CALL GEMINI
    # -------------------------
    response = model.generate_content(prompt)

    print("\n📊 ===== AI ANALYSIS =====\n")
    print(response.text)


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    main()