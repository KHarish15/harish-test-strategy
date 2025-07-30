# Move all imports to the top of the file
import os
import io
import re
import csv
import json
import time
import traceback
import warnings
import requests
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fpdf import FPDF
from docx import Document
from dotenv import load_dotenv
from atlassian import Confluence
import google.generativeai as genai
from bs4 import BeautifulSoup
from io import BytesIO
import difflib
import base64
from datetime import datetime
from flowchart_generator import generate_flowchart_image
from jira_utils import create_jira_issue
from slack_utils import send_slack_message

# Load environment variables
load_dotenv()

app = FastAPI(title="Confluence AI Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-v2ah.onrender.com",  # your frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
GEMINI_API_KEY = os.getenv("GENAI_API_KEY_1") or os.getenv("GENAI_API_KEY_2")
if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found in environment variables. Please set GENAI_API_KEY_1 or GENAI_API_KEY_2 in your .env file.")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Pydantic models for request/response
class SearchRequest(BaseModel):
    space_key: str
    page_title: str
    query: str

class VideoRequest(BaseModel):
    video_url: Optional[str] = None
    space_key: str
    page_title: str
    question: Optional[str] = None

class CodeRequest(BaseModel):
    space_key: str
    page_title: str
    instruction: str
    target_language: Optional[str] = None

class ImpactRequest(BaseModel):
    space_key: str
    old_page_title: str
    new_page_title: str
    question: Optional[str] = None

class TestRequest(BaseModel):
    space_key: str
    code_page_title: str
    test_input_page_title: Optional[str] = None
    question: Optional[str] = None

class ImageRequest(BaseModel):
    space_key: str
    page_title: str
    image_url: str

class ImageSummaryRequest(BaseModel):
    space_key: str
    page_title: str
    image_url: str
    summary: str
    question: str

class ChartRequest(BaseModel):
    space_key: str
    page_title: str
    image_url: str
    chart_type: str
    filename: str
    format: str

class ExportRequest(BaseModel):
    content: str
    format: str
    filename: str

class SaveToConfluenceRequest(BaseModel):
    space_key: Optional[str] = None
    page_title: str
    content: str
    mode: Optional[str] = "append"  # "append", "overwrite", "replace_section"
    heading_text: Optional[str] = None  # Used if mode == "replace_section"

class MeetingNotesRequest(BaseModel):
    space_key: str
    page_title: str
    meeting_notes: str
    confluence_page_id: Optional[str] = None
    confluence_space_key: Optional[str] = None

# Helper functions
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    no_emoji = emoji_pattern.sub(r'', text)
    return no_emoji.encode('latin-1', 'ignore').decode('latin-1')

def clean_html(html_content):
    """Clean HTML content and extract only the essential text/code"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Try to find code blocks first
    code_blocks = soup.find_all(['pre', 'code', 'ac:structured-macro'])
    if code_blocks:
        # Extract text from code blocks
        code_texts = []
        for block in code_blocks:
            text = block.get_text().strip()
            if text:
                code_texts.append(text)
        
        if code_texts:
            return '\n\n'.join(code_texts)
    
    # If no code blocks, get all text but limit it
    text = soup.get_text(separator="\n")
    
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Limit to reasonable size for CircleCI
    if len(text) > 2000:
        text = text[:2000] + "\n\n# ... Content truncated (original was too large)"
    
    return text

def init_confluence():
    try:
        return Confluence(
            url=os.getenv('CONFLUENCE_BASE_URL'),
            username=os.getenv('CONFLUENCE_USER_EMAIL'),
            password=os.getenv('CONFLUENCE_API_KEY'),
            timeout=10
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confluence initialization failed: {str(e)}")

# Export functions
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    return io.BytesIO(pdf.output(dest='S').encode('latin1'))

def create_docx(text):
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_csv(text):
    output = io.StringIO()
    writer = csv.writer(output)
    for line in text.strip().split('\n'):
        writer.writerow([line])
    return io.BytesIO(output.getvalue().encode())

def create_json(text):
    return io.BytesIO(json.dumps({"response": text}, indent=4).encode())

def create_html(text):
    html = f"<html><body><pre>{text}</pre></body></html>"
    return io.BytesIO(html.encode())

def create_txt(text):
    return io.BytesIO(text.encode())


def extract_timestamps_from_summary(summary):
    timestamps = []
    lines = summary.splitlines()
    collecting = False
    for line in lines:
        if "**Timestamps:**" in line or "Timestamps:" in line:
            collecting = True
            continue
        if collecting:
            if not line.strip() or line.strip().startswith("**"):
                break
            # match lines like "* [00:00-00:05] sentence" or "[00:00-00:05] sentence"
            match = re.match(r"^\*?\s*\[(\d{1,2}:\d{2}-\d{1,2}:\d{2})\]\s*(.*)", line.strip())
            if match:
                timestamp_text = f"[{match.group(1)}] {match.group(2)}"
                timestamps.append(timestamp_text)
            elif line.strip().startswith("*") or line.strip().startswith("-"):
                # fallback for bullet points
                timestamps.append(line.strip().lstrip("* -").strip())
            elif line.strip():
                # fallback for any non-empty line
                timestamps.append(line.strip())
    return timestamps

def auto_detect_space(confluence, space_key: Optional[str] = None) -> str:
    """
    If space_key is provided and valid, return it.
    If not provided, auto-detect:
      - If only one space exists, return its key.
      - If multiple, raise error to specify.
    """
    if space_key:
        return space_key
    
    print(f"🔍 Auto-detecting Confluence space...")
    try:
        spaces = confluence.get_all_spaces(start=0, limit=100)["results"]
        print(f"✅ Found {len(spaces)} spaces")
        if len(spaces) == 1:
            space_key = spaces[0]["key"]
            print(f"✅ Auto-detected space: {space_key}")
            return space_key
        else:
            print(f"⚠️ Multiple spaces found: {[s['key'] for s in spaces]}")
            raise HTTPException(status_code=400, detail="Multiple spaces found. Please specify a space_key.")
    except Exception as e:
        print(f"❌ Failed to auto-detect space: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to auto-detect space: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Confluence AI Assistant API", "status": "running"}

@app.get("/spaces")
async def get_spaces():
    """Get all available Confluence spaces"""
    try:
        confluence = init_confluence()
        
        spaces = confluence.get_all_spaces(start=0, limit=100)["results"]
        space_options = [{"name": s['name'], "key": s['key']} for s in spaces]
        
        return {"spaces": space_options}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages/{space_key}")
async def get_pages(space_key: Optional[str] = None):
    """Get all pages from a specific space (auto-detect if not provided)"""
    try:
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, space_key)
        
        pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
        page_titles = [p["title"] for p in pages]
        
        return {"pages": page_titles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def ai_powered_search(request: SearchRequest, req: Request):
    """AI Powered Search functionality"""
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, getattr(request, 'space_key', None))

        # Get the single page by title
        pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
        selected_page = next((p for p in pages if p["title"] == request.page_title), None)
        if not selected_page:
            raise HTTPException(status_code=400, detail="Page not found")

        # Extract content from the selected page
        page_id = selected_page["id"]
        page_data = confluence.get_page_by_id(page_id, expand="body.storage")
        raw_html = page_data["body"]["storage"]["value"]
        text_content = clean_html(raw_html)
        full_context = f"\n\nTitle: {selected_page['title']}\n{text_content}"

        # Generate AI response
        prompt = (
            f"Answer the following question using the provided Confluence page content as context.\n"
            f"Context:\n{full_context}\n\n"
            f"Question: {request.query}\n"
            f"Instructions: Begin with the answer based on the context above. Then, if applicable, supplement with general knowledge."
        )

        response = ai_model.generate_content(prompt)
        ai_response = response.text.strip()

        return {
            "response": ai_response,
            "page_analyzed": selected_page["title"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video-summarizer")
async def video_summarizer(request: VideoRequest, req: Request):
    """Video Summarizer functionality using AssemblyAI and Gemini"""
    import requests
    import tempfile
    import subprocess
    import shutil
    confluence = init_confluence()
    space_key = auto_detect_space(confluence, getattr(request, 'space_key', None))

    # Get page info
    pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
    selected_page = next((p for p in pages if p["title"] == request.page_title), None)
    if not selected_page:
        raise HTTPException(status_code=400, detail="Page not found")
    page_id = selected_page["id"]

    # Get attachments
    attachments = confluence.get(f"/rest/api/content/{page_id}/child/attachment?limit=50")
    video_attachment = None
    for att in attachments.get("results", []):
        if att["title"].lower().endswith(".mp4"):
            video_attachment = att
            break
    if not video_attachment:
        raise HTTPException(status_code=404, detail="No .mp4 video attachment found on this page.")

    # Download video
    video_url = video_attachment["_links"]["download"]
    full_url = f"{os.getenv('CONFLUENCE_BASE_URL').rstrip('/')}{video_url}"
    video_name = video_attachment["title"].replace(" ", "_")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, video_name)
        audio_path = os.path.join(tmpdir, "audio.mp3")
        # Download video file
        video_data = confluence._session.get(full_url).content
        with open(video_path, "wb") as f:
            f.write(video_data)
        # Extract audio using ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "mp3", audio_path
            ], check=True, capture_output=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ffmpeg audio extraction failed: {e}")
        # Upload audio to AssemblyAI
        assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not assemblyai_api_key:
            raise HTTPException(status_code=500, detail="AssemblyAI API key not configured. Please set ASSEMBLYAI_API_KEY in your environment variables.")
        headers = {"authorization": assemblyai_api_key}
        with open(audio_path, "rb") as f:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers=headers,
                data=f
            )
        if upload_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to upload audio to AssemblyAI")
        audio_url = upload_response.json()["upload_url"]
        # Submit for transcription
        transcript_request = {
            "audio_url": audio_url,
            "speaker_labels": True,
            "auto_chapters": True,
            "auto_highlights": True,
            "entity_detection": True,
            "sentiment_analysis": True
        }
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json=transcript_request,
            headers={**headers, "content-type": "application/json"}
        )
        if transcript_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to submit audio for transcription")
        transcript_id = transcript_response.json()["id"]
        # Poll for completion
        while True:
            polling_response = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=headers
            )
            if polling_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get transcription status")
            status = polling_response.json()["status"]
            if status == "completed":
                break
            elif status == "error":
                raise HTTPException(status_code=500, detail="Transcription failed")
            time.sleep(3)
        transcript_data = polling_response.json()
        transcript_text = transcript_data.get("text", "")
        if not transcript_text:
            raise HTTPException(status_code=500, detail="No transcript text returned from AssemblyAI")
        
        # Initialize Gemini AI model for text generation
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        
        # Q&A
        if request.question:
            qa_prompt = (
                f"Based on the following video transcript, answer this question: {request.question}\n\n"
                f"Transcript: {transcript_text[:3000]}\n\n"
                f"Provide a detailed answer based on the video content."
            )
            qa_response = ai_model.generate_content(qa_prompt)
            return {"answer": qa_response.text.strip()}
        
        # Generate quotes
        quote_prompt = (
            "Extract 3-5 powerful or interesting quotes from the transcript.\n"
            "Format each quote on a new line starting with a dash (-).\n"
            f"Transcript:\n{transcript_text[:3000]}"
        )
        quotes_response = ai_model.generate_content(quote_prompt).text.strip()
        # Split quotes into individual items
        quotes = [quote.strip().lstrip("- ").strip() for quote in quotes_response.split('\n') if quote.strip()]
        
        # Generate summary WITHOUT timestamps
        summary_prompt = (
            "detailed paragraph summarizing the video content.\n"
            "Do NOT include any timestamps in the summary.\n"
            f"Transcript:\n{transcript_text[:3000]}"
        )
        summary = ai_model.generate_content(summary_prompt).text.strip()
        
        # Generate timestamps separately
        timestamp_prompt = (
            "Extract 5-7 important moments from the following transcript.\n"
            "Format each moment as: [MM:SS-MM:SS] Description of what happens\n"
            "Example: [00:15-00:30] Speaker introduces the main topic\n"
            "Return only the timestamps, one per line.\n\n"
            f"Transcript:\n{transcript_text[:3000]}"
        )
        timestamps_response = ai_model.generate_content(timestamp_prompt).text.strip()
        # Split timestamps into individual items
        timestamps = [ts.strip() for ts in timestamps_response.split('\n') if ts.strip()]
        
        return {
            "summary": summary,
            "quotes": quotes,
            "timestamps": timestamps,
            "qa": [],
            "page_title": request.page_title,
            "transcript": transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text,
            "video_url": full_url
        }


@app.post("/code-assistant")
async def code_assistant(request: CodeRequest, req: Request):
    """Code Assistant functionality"""
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, getattr(request, 'space_key', None))
        
        # Get page content
        pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
        selected_page = next((p for p in pages if p["title"] == request.page_title), None)
        
        if not selected_page:
            raise HTTPException(status_code=400, detail="Page not found")
        
        page_id = selected_page["id"]
        page_content = confluence.get_page_by_id(page_id, expand="body.storage")
        context = page_content["body"]["storage"]["value"]
        
        # Extract visible code
        soup = BeautifulSoup(context, "html.parser")
        for tag in soup.find_all(['pre', 'code']):
            code_text = tag.get_text()
            if code_text.strip():
                cleaned_code = code_text
                break
        else:
            cleaned_code = soup.get_text(separator="\n").strip()
        
        # Detect language
        def detect_language_from_content(content: str) -> str:
            if "<?xml" in content:
                return "xml"
            if "<html" in content.lower() or "<!DOCTYPE html>" in content:
                return "html"
            if content.strip().startswith("{") or content.strip().startswith("["):
                return "json"
            if re.search(r"\bclass\s+\w+", content) and "public" in content:
                return "java"
            if "#include" in content:
                return "cpp"
            if "def " in content:
                return "python"
            if "function" in content or "=>" in content:
                return "javascript"
            return "text"
        
        detected_lang = detect_language_from_content(cleaned_code)
        
        # Generate summary
        summary_prompt = (
            f"The following is content (possibly code or structure) from a Confluence page:\n\n{context}\n\n"
            "Summarize in detailed paragraph"
        )
        summary_response = ai_model.generate_content(summary_prompt)
        summary = summary_response.text.strip()
        
        # Modify code if instruction provided
        modified_code = None
        if request.instruction:
            alteration_prompt = (
                f"The following is a piece of code extracted from a Confluence page:\n\n{cleaned_code}\n\n"
                f"Please modify this code according to the following instruction:\n'{request.instruction}'\n\n"
                "Return the modified code only. No explanation or extra text."
            )
            altered_response = ai_model.generate_content(alteration_prompt)
            modified_code = re.sub(r"^```[a-zA-Z]*\n|```$", "", altered_response.text.strip(), flags=re.MULTILINE)
        
        # Convert to another language if requested
        converted_code = None
        if request.target_language and request.target_language != detected_lang:
            input_code = modified_code if modified_code else cleaned_code
            convert_prompt = (
                f"The following is a code structure or data snippet:\n\n{input_code}\n\n"
                f"Convert this into equivalent {request.target_language} code. Only show the converted code."
            )
            lang_response = ai_model.generate_content(convert_prompt)
            converted_code = re.sub(r"^```[a-zA-Z]*\n|```$", "", lang_response.text.strip(), flags=re.MULTILINE)
        
        return {
            "summary": summary,
            "original_code": cleaned_code,
            "detected_language": detected_lang,
            "modified_code": modified_code,
            "converted_code": converted_code,
            "target_language": request.target_language
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/impact-analyzer")
async def impact_analyzer(request: ImpactRequest, req: Request):
    """Impact Analyzer functionality"""
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, getattr(request, 'space_key', None))
        
        # Get pages
        pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
        old_page = next((p for p in pages if p["title"] == request.old_page_title), None)
        new_page = next((p for p in pages if p["title"] == request.new_page_title), None)
        
        if not old_page or not new_page:
            raise HTTPException(status_code=400, detail="One or both pages not found")
        
        # Extract content from pages
        def extract_content(content):
            soup = BeautifulSoup(content, 'html.parser')
            # Try to find code blocks first
            code_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'code'})
            if code_blocks:
                return '\n'.join(
                    block.find('ac:plain-text-body').text
                    for block in code_blocks if block.find('ac:plain-text-body')
                )
            # If no code blocks, extract all text content
            return soup.get_text(separator="\n").strip()
        
        old_raw = confluence.get_page_by_id(old_page["id"], expand="body.storage")["body"]["storage"]["value"]
        new_raw = confluence.get_page_by_id(new_page["id"], expand="body.storage")["body"]["storage"]["value"]
        old_content = extract_content(old_raw)
        new_content = extract_content(new_raw)
        
        if not old_content or not new_content:
            raise HTTPException(status_code=400, detail="No content found in one or both pages")
        
        # Generate diff
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        diff = difflib.unified_diff(old_lines, new_lines, fromfile=request.old_page_title, tofile=request.new_page_title, lineterm='')
        full_diff_text = '\n'.join(diff)
        
        # Calculate metrics
        lines_added = sum(1 for l in full_diff_text.splitlines() if l.startswith('+') and not l.startswith('+++'))
        lines_removed = sum(1 for l in full_diff_text.splitlines() if l.startswith('-') and not l.startswith('---'))
        total_lines = len(old_lines) or 1
        percent_change = round(((lines_added + lines_removed) / total_lines) * 100, 2)
        
        # Generate AI analysis
        def clean_and_truncate_prompt(text, max_chars=10000):
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'[^\x00-\x7F]+', '', text)
            return text[:max_chars]
        
        safe_diff = clean_and_truncate_prompt(full_diff_text)
        
        # Impact analysis
        impact_prompt = f"""Write 2 paragraphs summarizing the overall impact of the following changes between two versions of a document.
        
        Cover only:
        - What was changed
        - Which parts of the content are affected
        - Why this matters
        
        Keep it within 20 sentences.
        
        Changes:
        {safe_diff}"""
        
        impact_response = ai_model.generate_content(impact_prompt)
        impact_text = impact_response.text.strip()
        
        # Recommendations
        rec_prompt = f"""As a senior analyst, write 2 paragraphs suggesting improvements for the following changes.

        Focus on:
        - Content quality
        - Clarity and completeness
        - Any possible enhancements
        
        Limit to 20 sentences.
        
        Changes:
        {safe_diff}"""
        
        rec_response = ai_model.generate_content(rec_prompt)
        rec_text = rec_response.text.strip()
        
        # Risk analysis
        risk_prompt = f"Assess the risk of each change in this document diff with severity tags (Low, Medium, High):\n\n{safe_diff}"
        risk_response = ai_model.generate_content(risk_prompt)
        raw_risk = risk_response.text.strip()
        risk_text = re.sub(
            r'\b(Low|Medium|High)\b',
            lambda m: {
                'Low': '🟢 Low',
                'Medium': '🟡 Medium',
                'High': '🔴 High'
            }[m.group(0)],
            raw_risk
        )
        
        # Generate structured risk factors (new dynamic part)
        risk_factors_prompt = f"""
        Analyze the following code/content diff and extract a structured list of key risk factors introduced by these changes.

        Focus on identifying:
        - Broken or removed validation
        - Modified authentication/authorization checks
        - Logical regressions
        - Removed error handling
        - Performance or scalability risks
        - Security vulnerabilities
        - Stability or maintainability concerns

        Write each risk factor as 1 line. Avoid repeating obvious stats like line count.

        Diff:
        {safe_diff}
        """

        risk_factors_response = ai_model.generate_content(risk_factors_prompt)
        risk_factors = risk_factors_response.text.strip().split("\n")
        risk_factors = [re.sub(r"^[\*\-•\s]+", "", line).strip() for line in risk_factors if line.strip()]



        # Q&A if question provided
        qa_answer = None
        if request.question:
            context = (
                f"Summary: {impact_text[:1000]}\n"
                f"Recommendations: {rec_text[:1000]}\n"
                f"Risks: {risk_text[:1000]}\n"
                f"Changes: +{lines_added}, -{lines_removed}, ~{percent_change}%"
            )
            qa_prompt = f"""You are an expert AI assistant. Based on the report below, answer the user's question clearly.

{context}

Question: {request.question}

Answer:"""
            qa_response = ai_model.generate_content(qa_prompt)
            qa_answer = qa_response.text.strip()
            
        
        result = {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "files_changed": 1,
            "percentage_change": percent_change,
            "impact_analysis": impact_text,
            "recommendations": rec_text,
            "risk_analysis": risk_text,
            "risk_level": "low" if percent_change < 10 else "medium" if percent_change < 30 else "high",
            "risk_score": min(10, max(1, round(percent_change / 10))),
            "risk_factors": risk_factors,
            "answer": qa_answer,
            "diff": full_diff_text
        }

        # Agentic Jira integration: create ticket if risk is high
        if result["risk_level"] == "high":
            try:
                print("Attempting to create Jira issue for high risk...")
                summary = f"High Risk Change Detected: {request.old_page_title} → {request.new_page_title}"
                description = (
                    f"Impact Analysis:\n{impact_text}\n\n"
                    f"Recommendations:\n{rec_text}\n\n"
                    f"Risk Analysis:\n{risk_text}\n\n"
                    f"Diff:\n{full_diff_text[:1000]}..."  # Truncate if too long
                )
                jira_result = create_jira_issue(summary, description)
                print(f"Jira issue created: {jira_result}")
                result["jira_issue"] = jira_result.get("key")
                jira_url = None
                if jira_result.get("key"):
                    jira_url = f"{os.getenv('JIRA_BASE_URL')}/browse/{jira_result['key']}"
            except Exception as jira_exc:
                print(f"Jira issue creation failed: {jira_exc}")
                result["jira_error"] = str(jira_exc)
                jira_url = None
            # Send Slack notification
            try:
                slack_message = (
                    "*High Risk Change Detected!*\n"
                    f"*Pages:* {request.old_page_title} → {request.new_page_title}\n"
                    f"*Risk Level:* HIGH\n"
                    f"*Summary:* {impact_text[:200]}...\n"
                    + (f"*Jira Ticket:* <{jira_url}|{jira_result.get('key')}>\n" if jira_url else "")
                )
                send_slack_message(slack_message)
                print("Slack notification sent.")
            except Exception as slack_exc:
                print(f"Slack notification failed: {slack_exc}")
                result["slack_error"] = str(slack_exc)

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CircleCI Integration Only ---
# CircleCI integration is handled via the .circleci/config.yml file
# which sends test results to /analyze-logs endpoint and posts to Confluence

import requests
import os
import json
from datetime import datetime
import uuid

# CircleCI API configuration
CIRCLECI_API_TOKEN = os.getenv('CIRCLECI_API_TOKEN', 'your-circleci-token')
CIRCLECI_PROJECT_SLUG = os.getenv('CIRCLECI_PROJECT_SLUG', 'github/KHarish15/finalmain')
CIRCLECI_API_BASE = "https://circleci.com/api/v2"

def trigger_circleci_pipeline(branch="main", parameters=None, code_content=None, test_content=None, code_filename=None, test_filename=None):
    """Trigger a new CircleCI pipeline with file content"""
    try:
        print(f"🔍 Checking CircleCI configuration...")
        print(f"🔍 API Token configured: {'Yes' if CIRCLECI_API_TOKEN and CIRCLECI_API_TOKEN != 'your-circleci-token' else 'No'}")
        print(f"🔍 Project Slug configured: {'Yes' if CIRCLECI_PROJECT_SLUG and CIRCLECI_PROJECT_SLUG != 'github/your-username/your-repo' else 'No'}")
        
        # Check if CircleCI is properly configured
        if CIRCLECI_API_TOKEN == 'your-circleci-token' or not CIRCLECI_API_TOKEN:
            print("⚠️ CircleCI not configured - skipping pipeline trigger")
            print("📋 To enable CircleCI integration, set these environment variables:")
            print("   CIRCLECI_API_TOKEN=your-actual-circleci-token")
            print("   CIRCLECI_PROJECT_SLUG=github/your-username/your-repo")
            return {
                "success": False,
                "error": "CircleCI not configured. Please set CIRCLECI_API_TOKEN and CIRCLECI_PROJECT_SLUG environment variables.",
                "setup_required": True
            }
        
        if CIRCLECI_PROJECT_SLUG == 'github/your-username/your-repo':
            print("⚠️ CircleCI project slug not configured - skipping pipeline trigger")
            print("📋 To enable CircleCI integration, set CIRCLECI_PROJECT_SLUG environment variable:")
            print("   CIRCLECI_PROJECT_SLUG=github/your-username/your-repo")
            return {
                "success": False,
                "error": "CircleCI project slug not configured. Please set CIRCLECI_PROJECT_SLUG environment variable.",
                "setup_required": True
            }
        
        url = f"{CIRCLECI_API_BASE}/project/{CIRCLECI_PROJECT_SLUG}/pipeline"
        
        headers = {
            "Circle-Token": CIRCLECI_API_TOKEN,
            "Content-Type": "application/json"
        }
        
        # Prepare payload with file content if provided
        payload = {
            "branch": branch
        }
        
        # Add file content parameters if provided
        if code_content:
            import base64
            
            # Function to truncate content to fit CircleCI limits
            def truncate_for_circleci(content, max_chars=350):
                """Truncate content to fit within CircleCI parameter limits"""
                if len(content) <= max_chars:
                    return content
                
                # For very large content, be more aggressive
                if len(content) > 1000:
                    max_chars = 250  # Even more conservative for very large files
                
                # Try to truncate at a logical point (end of line, function, etc.)
                truncated = content[:max_chars]
                
                # Try to find a good truncation point
                for separator in ['\n\n', '\n', ';', ' ']:
                    last_sep = truncated.rfind(separator)
                    if last_sep > max_chars * 0.8:  # At least 80% of max length
                        truncated = truncated[:last_sep + len(separator)]
                        break
                
                # Add truncation indicator
                truncated += f"\n\n# ... Content truncated for CircleCI (original: {len(content)} chars)"
                return truncated
            
            # Truncate code content if needed
            truncated_code = truncate_for_circleci(code_content)
            code_b64 = base64.b64encode(truncated_code.encode()).decode()
            
            print(f"🔍 DEBUG: Original code content size: {len(code_content)} chars")
            print(f"🔍 DEBUG: Truncated code content size: {len(truncated_code)} chars")
            print(f"🔍 DEBUG: Code base64 size: {len(code_b64)} chars")
            
            # Final safety check
            if len(code_b64) > 450:  # Leave more buffer for CircleCI's 512 limit
                print(f"⚠️ Code content still too large after truncation")
                print(f"📄 Code base64 size: {len(code_b64)} chars")
                print(f"📋 CircleCI limit: 512 chars per parameter")
                
                return {
                    "success": False,
                    "error": f"Code content too large for CircleCI parameters even after truncation. Code: {len(code_b64)} chars. CircleCI limit: 512 chars per parameter. Please use much smaller files.",
                    "setup_required": False
                }
            
            # Prepare parameters
            payload["parameters"] = {
                "code_content": code_b64,
                "code_filename": code_filename or "python_sample.py"
            }
            
            # Add test content if available
            if test_content:
                # Estimate base64 size before encoding
                estimated_b64_size = int(len(test_content) * 1.37)  # Base64 is ~37% larger
                print(f"🔍 DEBUG: Estimated test base64 size: {estimated_b64_size} chars")
                
                # Truncate test content if needed
                truncated_test = truncate_for_circleci(test_content)
                test_b64 = base64.b64encode(truncated_test.encode()).decode()
                
                print(f"🔍 DEBUG: Original test content size: {len(test_content)} chars")
                print(f"🔍 DEBUG: Truncated test content size: {len(truncated_test)} chars")
                print(f"🔍 DEBUG: Test base64 size: {len(test_b64)} chars")
                
                if len(test_b64) > 450:  # More conservative buffer for CircleCI's 512 limit
                    print(f"⚠️ Test content still too large after truncation")
                    print(f"🧪 Test base64 size: {len(test_b64)} chars")
                    print(f"📋 CircleCI limit: 512 chars per parameter")
                    
                    return {
                        "success": False,
                        "error": f"Test content too large for CircleCI parameters even after truncation. Test: {len(test_b64)} chars. CircleCI limit: 512 chars per parameter. Please use much smaller files.",
                        "setup_required": False
                    }
                
                payload["parameters"]["test_content"] = test_b64
                payload["parameters"]["test_filename"] = test_filename or "input_file.py"
                print(f"🚀 Triggering CircleCI pipeline with code and test content")
                print(f"📄 Code file: {code_filename or 'python_sample.py'}")
                print(f"🧪 Test file: {test_filename or 'input_file.py'}")
            else:
                print(f"🚀 Triggering CircleCI pipeline with code content only")
                print(f"📄 Code file: {code_filename or 'python_sample.py'}")
                print(f"⚠️ No test content - CircleCI will create basic test")
        else:
            print(f"🚀 Triggering CircleCI pipeline for branch: {branch}")
            print(f"⚠️ No code content provided - cannot proceed")
            return {
                "success": False,
                "error": "No code content provided. Please ensure code content is available.",
                "setup_required": False
            }
        
        print(f"📋 Payload: {payload}")
        print(f"🔗 CircleCI Dashboard URL: https://app.circleci.com/pipelines/{CIRCLECI_PROJECT_SLUG}")
        
        # Add better timeout and error handling
        try:
            print(f"🚀 Making CircleCI API request with 15-second timeout...")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print(f"✅ CircleCI API request completed in {response.elapsed.total_seconds():.2f} seconds")
        except requests.exceptions.Timeout:
            print(f"❌ CircleCI API request timed out after 15 seconds")
            return {
                "success": False,
                "error": "CircleCI API request timed out. The service may be down or experiencing issues.",
                "setup_required": False
            }
        except requests.exceptions.ConnectionError as e:
            print(f"❌ CircleCI API connection error: {e}")
            return {
                "success": False,
                "error": f"Failed to connect to CircleCI API: {str(e)}. Please check your internet connection.",
                "setup_required": False
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ CircleCI API request failed: {e}")
            return {
                "success": False,
                "error": f"CircleCI API request failed: {str(e)}",
                "setup_required": False
            }
        
        if response.status_code == 201:
            pipeline_data = response.json()
            pipeline_id = pipeline_data.get('id')
            build_number = pipeline_data.get('number')
            
            print(f"✅ CircleCI pipeline triggered successfully!")
            print(f"📋 Pipeline ID: {pipeline_id}")
            print(f"🔢 Build Number: {build_number}")
            print(f"🔗 Live Dashboard: https://app.circleci.com/pipelines/{CIRCLECI_PROJECT_SLUG}/{build_number}")
            print(f"📊 Build URL: https://app.circleci.com/pipelines/{pipeline_id}")
            
            # Send immediate notification to Confluence about the trigger
            try:
                confluence_notification = {
                    'space_key': 'TEST',  # Default space key
                    'page_title': f'CircleCI Build #{build_number} - Live Status',
                    'content': f'''
## 🚀 CircleCI Pipeline Triggered - Live Status

### Build Information
- **Build Number**: #{build_number}
- **Pipeline ID**: `{pipeline_id}`
- **Branch**: {branch}
- **Triggered At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Triggered By**: Test Support Tool

### Live Links
- **🔗 CircleCI Dashboard**: [View Live Build](https://app.circleci.com/pipelines/{CIRCLECI_PROJECT_SLUG}/{build_number})
- **📊 Pipeline Details**: [Pipeline #{build_number}](https://app.circleci.com/pipelines/{pipeline_id})

### Current Status
🔄 **Status**: Pipeline triggered, tests starting...

### What's Happening Now
1. **Test Suite Execution**: Running comprehensive test suite
2. **AI Analysis**: Analyzing test results with AI
3. **Coverage Report**: Generating test coverage reports
4. **Confluence Post**: Will post final results here

### Real-time Updates
This page will be updated as the pipeline progresses. Refresh to see latest status.

---
*Generated automatically by Test Support Tool with CircleCI integration*
'''
                }
                
                # Post immediate notification
                confluence = init_confluence()
                try:
                    confluence.create_page(
                        space=confluence_notification['space_key'],
                        title=confluence_notification['page_title'],
                        body=confluence_notification['content']
                    )
                    print(f"📄 Immediate notification posted to Confluence")
                except Exception as e:
                    print(f"⚠️ Could not post immediate notification: {e}")
                    
            except Exception as e:
                print(f"⚠️ Notification setup failed: {e}")
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "number": build_number,
                "state": pipeline_data.get('state'),
                "created_at": pipeline_data.get('created_at'),
                "dashboard_url": f"https://app.circleci.com/pipelines/{CIRCLECI_PROJECT_SLUG}/{build_number}",
                "pipeline_url": f"https://app.circleci.com/pipelines/{pipeline_id}"
            }
        else:
            error_msg = f"CircleCI API returned {response.status_code}: {response.text}"
            print(f"❌ Failed to trigger CircleCI pipeline: {error_msg}")
            
            # Provide helpful error messages
            if response.status_code == 401:
                error_msg = "Invalid CircleCI API token. Please check your CIRCLECI_API_TOKEN environment variable."
            elif response.status_code == 404:
                error_msg = "CircleCI project not found. Please check your CIRCLECI_PROJECT_SLUG environment variable."
            elif response.status_code == 403:
                error_msg = "CircleCI API token doesn't have permission to trigger pipelines."
            elif response.status_code == 400:
                error_msg = "Invalid request parameters. File content may be too large for CircleCI parameters."
            
            return {
                "success": False,
                "error": error_msg,
                "setup_required": True
            }
            
    except Exception as e:
        print(f"❌ Error triggering CircleCI pipeline: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "setup_required": True
        }

def get_circleci_pipeline_status(pipeline_id):
    """Get the status of a CircleCI pipeline"""
    try:
        url = f"{CIRCLECI_API_BASE}/pipeline/{pipeline_id}"
        
        headers = {
            "Circle-Token": CIRCLECI_API_TOKEN
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            pipeline_data = response.json()
            return {
                "success": True,
                "pipeline": pipeline_data
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get pipeline status: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_circleci_workflow_status(pipeline_id):
    """Get the status of workflows in a CircleCI pipeline"""
    try:
        url = f"{CIRCLECI_API_BASE}/pipeline/{pipeline_id}/workflow"
        
        headers = {
            "Circle-Token": CIRCLECI_API_TOKEN
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            workflows_data = response.json()
            return {
                "success": True,
                "workflows": workflows_data.get('items', [])
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get workflow status: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/trigger-circleci")
async def trigger_circleci_endpoint(request: Request):
    """Endpoint to trigger CircleCI pipeline"""
    try:
        data = await request.json()
        branch = data.get('branch', 'main')
        parameters = data.get('parameters', {})
        
        # Add timestamp and request ID for tracking
        parameters['request_id'] = str(uuid.uuid4())
        parameters['triggered_at'] = datetime.now().isoformat()
        parameters['trigger_source'] = 'test-support-tool'
        
        result = trigger_circleci_pipeline(branch, parameters)
        
        if result['success']:
            # Log the trigger for audit trail
            print(f"📊 CircleCI Pipeline Triggered:")
            print(f"   Pipeline ID: {result['pipeline_id']}")
            print(f"   Branch: {branch}")
            print(f"   Parameters: {parameters}")
            print(f"   Timestamp: {datetime.now().isoformat()}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in trigger-circleci endpoint: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/circleci-status/{pipeline_id}")
async def get_circleci_status(pipeline_id: str):
    """Get CircleCI pipeline and workflow status"""
    try:
        # Get pipeline status
        pipeline_status = get_circleci_pipeline_status(pipeline_id)
        
        # Get workflow status
        workflow_status = get_circleci_workflow_status(pipeline_id)
        
        return {
            "pipeline": pipeline_status,
            "workflows": workflow_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# --- Test Support Route Update ---
from fastapi import APIRouter, Request

# Removed duplicate router endpoint to fix conflicts

@app.post("/test-support")
async def test_support(request: TestRequest, req: Request):
    """Test Support Tool functionality with CircleCI integration"""
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        print(f"🔍 Configuring AI model...")
        try:
            genai.configure(api_key=api_key)
            ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
            print(f"✅ AI model configured successfully")
        except Exception as e:
            print(f"❌ Failed to configure AI model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to configure AI model: {str(e)}")
        print(f"Test support request: {request}")  # Debug log
        print(f"🔍 Initializing Confluence connection...")
        try:
            confluence = init_confluence()
            print(f"✅ Confluence connection established")
        except Exception as e:
            print(f"❌ Failed to initialize Confluence: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize Confluence: {str(e)}")
        
        space_key = auto_detect_space(confluence, getattr(request, 'space_key', None))
        
        # Get code page with timeout protection
        print(f"🔍 Fetching pages from Confluence space: {space_key}")
        try:
            pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=50)
            print(f"✅ Retrieved {len(pages)} pages from Confluence")
        except Exception as e:
            print(f"❌ Failed to fetch pages from Confluence: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch pages from Confluence: {str(e)}")
        
        code_page = next((p for p in pages if p["title"] == request.code_page_title), None)
        
        if not code_page:
            raise HTTPException(status_code=400, detail="Code page not found")
        
        print(f"Found code page: {code_page['title']}")  # Debug log
        
        print(f"🔍 Fetching code page content...")
        try:
            code_data = confluence.get_page_by_id(code_page["id"], expand="body.storage")
            code_content = code_data["body"]["storage"]["value"]
            print(f"✅ Retrieved code content ({len(code_content)} chars)")
        except Exception as e:
            print(f"❌ Failed to fetch code page content: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch code page content: {str(e)}")
        
        print(f"Code content length: {len(code_content)}")  # Debug log
        
        # Get test input page if provided
        test_content = None
        test_filename = None
        if request.test_input_page_title:
            test_page = next((p for p in pages if p["title"] == request.test_input_page_title), None)
            if test_page:
                print(f"🔍 Fetching test page content...")
                try:
                    test_data = confluence.get_page_by_id(test_page["id"], expand="body.storage")
                    test_content = test_data["body"]["storage"]["value"]
                    test_filename = f"{request.test_input_page_title}.py"
                    print(f"✅ Found test input page: {test_page['title']}")
                    print(f"✅ Test content length: {len(test_content)}")
                except Exception as e:
                    print(f"❌ Failed to fetch test page content: {e}")
                    print(f"⚠️ Continuing without test page content")
                    test_content = None
                    test_filename = None
            else:
                print(f"⚠️ Test input page '{request.test_input_page_title}' not found")
        else:
            print(f"📝 No test input page provided - will create basic test file")
            # Create a basic test file from the code content
            test_content = f"""import pytest
from {request.code_page_title.replace(' ', '_').lower()} import *

def test_basic():
    # Basic test to verify the code can be imported
    assert True
"""
            test_filename = f"test_{request.code_page_title.replace(' ', '_').lower()}.py"
            print(f"Created basic test file: {test_filename}")
        
        # 🚀 TRIGGER CIRCLECI PIPELINE WITH FILE CONTENT
        print("🚀 Triggering CircleCI pipeline with file content...")
        
        # Clean code content (remove HTML tags if present)
        clean_code_content = clean_html(code_content)
        clean_test_content = clean_html(test_content) if test_content else None
        
        # Debug: Show content sizes
        print(f"📄 Clean code content length: {len(clean_code_content)}")
        if clean_test_content:
            print(f"🧪 Clean test content length: {len(clean_test_content)}")
        else:
            print(f"🧪 No test content available")
        
        # Early size check to prevent CircleCI issues
        def estimate_base64_size(content):
            """Estimate base64 size of content"""
            if not content:
                return 0
            # Base64 encoding increases size by ~33%
            return int(len(content) * 1.4)
        
        code_b64_estimate = estimate_base64_size(clean_code_content)
        test_b64_estimate = estimate_base64_size(clean_test_content)
        
        print(f"🔍 Estimated base64 sizes - Code: {code_b64_estimate} chars, Test: {test_b64_estimate} chars")
        
        # If content is too large, truncate it before sending to CircleCI
        if code_b64_estimate > 400:  # More conservative buffer for CircleCI's 512 limit
            print(f"⚠️ Code content too large for CircleCI, truncating...")
            # Truncate to ~250 chars to account for base64 expansion
            clean_code_content = clean_code_content[:250] + "\n\n# ... Content truncated for CircleCI compatibility"
            print(f"📄 Truncated code content length: {len(clean_code_content)}")
        
        if test_b64_estimate > 400:
            print(f"⚠️ Test content too large for CircleCI, truncating...")
            clean_test_content = clean_test_content[:250] + "\n\n# ... Content truncated for CircleCI compatibility"
            print(f"🧪 Truncated test content length: {len(clean_test_content)}")
        
        # Clean filenames - remove spaces and ensure proper extension
        clean_code_filename = request.code_page_title.replace(' ', '_')
        if not clean_code_filename.endswith('.py'):
            clean_code_filename += '.py'
        
        clean_test_filename = test_filename
        if clean_test_filename:
            clean_test_filename = clean_test_filename.replace(' ', '_')
            if not clean_test_filename.endswith('.py'):
                clean_test_filename += '.py'
        
        print(f"🔍 Debug: Clean code filename: {clean_code_filename}")
        print(f"🔍 Debug: Clean test filename: {clean_test_filename}")
        
        # Check if CircleCI is configured before attempting to trigger
        if CIRCLECI_API_TOKEN == 'your-circleci-token' or not CIRCLECI_API_TOKEN:
            print("⚠️ CircleCI not configured - skipping pipeline trigger and continuing with AI analysis")
            circleci_result = {
                "success": False,
                "error": "CircleCI not configured. Please set CIRCLECI_API_TOKEN environment variable.",
                "setup_required": True,
                "note": "CircleCI integration skipped, but AI analysis continues"
            }
        else:
            circleci_result = trigger_circleci_pipeline(
                branch="main",
                code_content=clean_code_content,
                test_content=clean_test_content,
                code_filename=clean_code_filename,
                test_filename=clean_test_filename
            )
            
            if not circleci_result['success']:
                print(f"⚠️ CircleCI trigger failed: {circleci_result['error']}")
                # Continue with AI generation even if CircleCI fails
                # Add a note about the CircleCI failure to the response
                circleci_result['note'] = "CircleCI integration failed, but AI analysis continues"
        
        # Generate test strategy
        prompt_strategy = f"""The following is a code snippet:\n\n{code_content[:2000]}\n\nPlease generate a **structured test strategy** for the above code using the following format. 

Make sure each section heading is **clearly labeled** and includes a **percentage estimate** of total testing effort and the total of all percentage values across Unit Test, Integration Test, and End-to-End (E2E) Test must add up to exactly **100%**. Each subpoint should be short (1–2 lines max). Use bullet points for clarity.

---

## Unit Test (xx%)
- **Coverage Areas**:  
  - What functions or UI elements are directly tested?  
- **Edge Cases**:  
  - List 2–3 specific edge conditions or unusual inputs.

## Integration Test (xx%)
- **Integrated Modules**:  
  - What parts of the system work together and need testing as a unit?  
- **Data Flow Validation**:  
  - How does data move between components or layers?

## End-to-End (E2E) Test (xx%)
- **User Scenarios**:  
  - Provide 2–3 user flows that simulate real usage.  
- **System Dependencies**:  
  - What systems, APIs, or services must be operational?

## Test Data Management
- **Data Requirements**:  
  - What test data (e.g., users, tokens, inputs) is needed?  
- **Data Setup & Teardown**:  
  - How is test data created and cleaned up?

## Risk Assessment
- **High-Risk Areas**:  
  - Which parts of the code are most likely to fail?  
- **Mitigation Strategies**:  
  - How can we reduce testing risks?

## Test Environment Setup
- **Required Tools**:  
  - What testing frameworks and tools are needed?  
- **Configuration**:  
  - What environment variables or settings are required?

## Timeline Estimation
- **Development Time**:  
  - How long will it take to write these tests?  
- **Execution Time**:  
  - How long will the test suite take to run?

Please ensure the percentages add up to 100% and provide specific, actionable recommendations."""
        
        print(f"🤖 Generating test strategy with AI...")
        try:
            response_strategy = ai_model.generate_content(prompt_strategy)
            strategy_content = response_strategy.text
            print(f"✅ Test strategy generated successfully")
        except Exception as e:
            print(f"❌ AI strategy generation failed: {e}")
            strategy_content = "Error generating test strategy. Please try again."
        
        # Generate cross-platform testing strategy
        prompt_cross_platform = f"""Based on the code:\n\n{code_content[:2000]}\n\nGenerate a **cross-platform testing strategy** covering:

## Browser Compatibility
- **Supported Browsers**: Chrome, Firefox, Safari, Edge
- **Version Testing**: Latest 2 versions of each browser
- **Mobile Browsers**: iOS Safari, Chrome Mobile

## Operating System Testing
- **Desktop OS**: Windows, macOS, Linux
- **Mobile OS**: iOS, Android
- **Virtualization**: Docker containers for consistency

## Device Testing
- **Desktop**: Different screen resolutions (1920x1080, 1366x768, 2560x1440)
- **Tablet**: iPad, Android tablets
- **Mobile**: iPhone, Android phones (portrait and landscape)

## Accessibility Testing
- **Screen Readers**: NVDA, JAWS, VoiceOver
- **Keyboard Navigation**: Tab order, shortcuts
- **Color Contrast**: WCAG 2.1 AA compliance

## Performance Testing
- **Load Testing**: Multiple concurrent users
- **Stress Testing**: System limits
- **Network Conditions**: Slow 3G, fast WiFi, offline mode

## Security Testing
- **Authentication**: Different user roles
- **Data Validation**: Input sanitization
- **API Security**: Rate limiting, CORS

Provide specific test scenarios and tools for each category."""
        
        print(f"🤖 Generating cross-platform testing strategy...")
        try:
            response_cross_platform = ai_model.generate_content(prompt_cross_platform)
            cross_platform_content = response_cross_platform.text
            print(f"✅ Cross-platform strategy generated successfully")
        except Exception as e:
            print(f"❌ AI cross-platform generation failed: {e}")
            cross_platform_content = "Error generating cross-platform strategy. Please try again."
        
        # Generate test sensitivity analysis
        prompt_sensitivity = f"""Analyze the following code for **test sensitivity** and **flaky test prevention**:

{code_content[:2000]}

Provide a comprehensive analysis covering:

## Flaky Test Identification
- **Time-dependent operations**: Date/time functions, delays
- **External dependencies**: API calls, database connections
- **State management**: Shared state, cleanup issues
- **Concurrency issues**: Race conditions, async operations

## Test Isolation Strategies
- **Mocking strategies**: What to mock and how
- **Test data management**: Isolated test data
- **Environment setup**: Clean environment per test
- **Teardown procedures**: Proper cleanup

## Deterministic Testing
- **Fixed timestamps**: Use specific dates/times
- **Controlled randomness**: Seed random generators
- **Stable identifiers**: Use consistent IDs
- **Order-independent tests**: Avoid test dependencies

## Monitoring and Detection
- **Flaky test detection**: Tools and techniques
- **Retry strategies**: When and how to retry
- **Failure analysis**: Root cause investigation
- **Metrics tracking**: Success rate monitoring

## Prevention Best Practices
- **Code review guidelines**: What to look for
- **Testing patterns**: Anti-patterns to avoid
- **CI/CD integration**: Pipeline considerations
- **Documentation**: Test requirements and assumptions

Provide specific examples and code snippets for each category."""
        
        print(f"🤖 Generating test sensitivity analysis...")
        try:
            response_sensitivity = ai_model.generate_content(prompt_sensitivity)
            sensitivity_content = response_sensitivity.text
            print(f"✅ Sensitivity analysis generated successfully")
        except Exception as e:
            print(f"❌ AI sensitivity analysis failed: {e}")
            sensitivity_content = "Error generating sensitivity analysis. Please try again."
        
        # Prepare response with CircleCI information
        result = {
            "strategy": strategy_content,
            "cross_platform": cross_platform_content,
            "sensitivity": sensitivity_content,
            "circleci_trigger": circleci_result
        }
        
        # Add helpful guidance if CircleCI failed due to size issues
        if not circleci_result.get('success') and 'too large' in circleci_result.get('error', ''):
            result['guidance'] = {
                'message': 'CircleCI integration failed due to content size limits',
                'suggestions': [
                    'Use smaller code files or snippets',
                    'Split large files into smaller components',
                    'Remove unnecessary comments or whitespace',
                    'Focus on the core functionality for testing'
                ],
                'note': 'AI analysis completed successfully despite CircleCI failure'
            }
        
        # Log the complete operation
        print(f"✅ Test strategy generation completed:")
        print(f"   CircleCI Pipeline ID: {circleci_result.get('pipeline_id', 'N/A')}")
        print(f"   Strategy Length: {len(strategy_content)} chars")
        print(f"   Cross-Platform Length: {len(cross_platform_content)} chars")
        print(f"   Sensitivity Length: {len(sensitivity_content)} chars")
        
        return result
        
    except Exception as e:
        print(f"Error in test support: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-logs")
async def analyze_logs(request: Request):
    """Analyze test logs with AI and provide insights"""
    try:
        api_key = get_actual_api_key_from_identifier(request.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        
        # Get test results from request
        body = await request.json()
        test_results = body.get('test_results', {})
        
        # Create AI prompt for log analysis
        prompt = f"""
        Analyze the following test results and provide insights:
        
        Test Results: {test_results}
        
        Please provide:
        1. Summary of test execution
        2. Root cause analysis for any failures
        3. Recommendations for fixing issues
        4. Suggestions for improving test coverage
        5. Next steps for the development team
        
        Format your response in a clear, structured manner.
        """
        
        response = ai_model.generate_content(prompt)
        analysis = response.text.strip()
        
        return {
            "analysis": analysis,
            "test_results": test_results
        }
        
    except Exception as e:
        print(f"Log analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-to-confluence")
async def save_to_confluence(request: SaveToConfluenceRequest, req: Request):
    """
    Update the content of a Confluence page (storage format).
    Supports append, overwrite, and replace_section modes.
    """
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        confluence = init_confluence()
        
        # Validate required fields
        if not request.space_key:
            raise HTTPException(status_code=400, detail="space_key is required")
        if not request.page_title:
            raise HTTPException(status_code=400, detail="page_title is required")
        if not request.content:
            raise HTTPException(status_code=400, detail="content is required")
        
        space_key = auto_detect_space(confluence, request.space_key)
        
        # Get page by title, expand body.storage
        try:
            page = confluence.get_page_by_title(space=space_key, title=request.page_title, expand='body.storage')
            if not page:
                raise HTTPException(status_code=404, detail=f"Page '{request.page_title}' not found in space '{space_key}'")
        except Exception as e:
            if "permission" in str(e).lower() or "access" in str(e).lower():
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied. The calling user does not have permission to view the content in space '{space_key}'. Please check your Confluence API credentials and permissions."
                )
            elif "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=f"Page '{request.page_title}' not found in space '{space_key}'")
            else:
                raise HTTPException(status_code=500, detail=f"Error accessing Confluence: {str(e)}")
        
        page_id = page["id"]
        existing_content = page["body"]["storage"]["value"]
        updated_body = existing_content
        
        if request.mode == "overwrite":
            updated_body = request.content
        elif request.mode == "replace_section":
            if not request.heading_text:
                raise HTTPException(status_code=400, detail="heading_text must be provided for replace_section mode.")
            # Find the section by heading and replace its content
            heading_pattern = re.compile(rf"(<h[1-6][^>]*>\s*{re.escape(request.heading_text)}\s*</h[1-6]>)(.*?)(?=<h[1-6][^>]*>|$)", re.DOTALL | re.IGNORECASE)
            def replacer(match):
                return f"{match.group(1)}\n{request.content}\n"
            new_content, count = heading_pattern.subn(replacer, existing_content, count=1)
            if count == 0:
                raise HTTPException(status_code=404, detail=f"Heading '{request.heading_text}' not found in page.")
            updated_body = new_content
        else:  # append (default)
            change_log = (
                f"<p style='color:gray;font-size:smaller;margin:0;'>"
                f"<strong>🕒 Updated by AI Assistant on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>"
                f"</p>"
            )
            updated_body = existing_content + "<hr/>" + request.content + "\n" + change_log
        
        # Update page (only once, after change_log is added)
        try:
            confluence.update_page(
                page_id=page_id,
                title=request.page_title,
                body=updated_body,
                representation="storage"
            )
        except Exception as e:
            if "permission" in str(e).lower() or "access" in str(e).lower():
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied. The calling user does not have permission to update the page '{request.page_title}' in space '{space_key}'. Please check your Confluence API credentials and permissions."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Error updating page: {str(e)}")
        
        return {
            "message": "Page updated successfully",
            "previous_version": existing_content  # This is the backup of the old content
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Test support error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preview-save-to-confluence")
async def preview_save_to_confluence(request: SaveToConfluenceRequest, req: Request):
    """
    Preview the result of saving to Confluence. Returns the updated content and a diff, but does not save.
    """
    try:
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, request.space_key)
        page = confluence.get_page_by_title(space=space_key, title=request.page_title, expand='body.storage')
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        existing_content = page["body"]["storage"]["value"]
        updated_body = existing_content
        if request.mode == "overwrite":
            updated_body = request.content
        elif request.mode == "replace_section":
            if not request.heading_text:
                raise HTTPException(status_code=400, detail="heading_text must be provided for replace_section mode.")
            heading_pattern = re.compile(rf"(<h[1-6][^>]*>\s*{re.escape(request.heading_text)}\s*</h[1-6]>)(.*?)(?=<h[1-6][^>]*>|$)", re.DOTALL | re.IGNORECASE)
            def replacer(match):
                return f"{match.group(1)}\n{request.content}\n"
            new_content, count = heading_pattern.subn(replacer, existing_content, count=1)
            if count == 0:
                raise HTTPException(status_code=404, detail=f"Heading '{request.heading_text}' not found in page.")
            updated_body = new_content
        else:  # append (default)
            updated_body = existing_content + "<hr/>" + request.content
        # Generate diff
        diff = list(difflib.unified_diff(
            existing_content.splitlines(),
            updated_body.splitlines(),
            fromfile='current',
            tofile='preview',
            lineterm='' 
        ))
        return {
            "preview_content": request.content,
            "diff": "\n".join(diff)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flowchart-generator")
async def flowchart_generator(space_key: Optional[str] = Body(None), page_title: str = Body(...), req: Request = None):
    """Generate flowchart from Confluence page content"""
    try:
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, space_key)
        
        # Get page content
        pages = confluence.get_all_pages_from_space(space=space_key, start=0, limit=100)
        selected_page = next((p for p in pages if p["title"] == page_title), None)
        if not selected_page:
            raise HTTPException(status_code=400, detail="Page not found")
        
        page_content = confluence.get_page_by_id(selected_page["id"], expand="body.storage")
        content = page_content["body"]["storage"]["value"]
        
        # Clean HTML content
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
        
        # Generate flowchart
        flowchart_image = generate_flowchart_image(text_content)
        
        return {
            "flowchart_image": flowchart_image,
            "page_title": page_title,
            "space_key": space_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flowchart: {str(e)}")

@app.post("/meeting-notes-extractor")
async def meeting_notes_extractor(request: MeetingNotesRequest, req: Request):
    """Extract action items from meeting notes and create Jira issues, update Confluence, and notify Slack"""
    try:
        # Initialize Gemini AI
        api_key = get_actual_api_key_from_identifier(req.headers.get('x-api-key'))
        genai.configure(api_key=api_key)
        ai_model = genai.GenerativeModel("models/gemini-1.5-flash-8b-latest")
        
        # Extract tasks using Gemini AI
        prompt = f"""
You are an assistant extracting action items from meeting notes.

Please respond ONLY with a JSON array in this exact format, without any extra text or explanation:
[
  {{
    "task": "Task description",
    "assignee": "Person responsible",
    "due": "YYYY-MM-DD"
  }}
]

Meeting Notes:
{request.meeting_notes}
"""
        
        response = ai_model.generate_content(prompt)
        output = response.text.strip()
        
        # Clean up the response
        if output.startswith("```"):
            output = output.split("```")[1].strip()
            if output.lower().startswith("json"):
                output = "\n".join(output.split("\n")[1:]).strip()
        
        tasks = json.loads(output)
        
        # Initialize Confluence
        confluence = init_confluence()
        space_key = auto_detect_space(confluence, request.space_key)
        
        # Process each task
        processed_tasks = []
        
        for task in tasks:
            try:
                # Create Jira issue using existing jira_utils
                jira_response = create_jira_issue(
                    summary=task["task"],
                    description=f"Auto-created from meeting notes. Due: {task['due']}",
                    issue_type="Task"
                )
                
                if jira_response and 'key' in jira_response:
                    # Extract just the issue key from the response
                    issue_key = jira_response['key']
                    # Get Jira issue details
                    jira_base_url = os.getenv('JIRA_BASE_URL')
                    jira_link = f"{jira_base_url}/browse/{issue_key}"
                    
                    # Add Jira link to task
                    task_with_link = {**task, "jira_key": issue_key, "jira_link": jira_link}
                    processed_tasks.append(task_with_link)
                    
                    # Send Slack notification using existing slack_utils
                    slack_message = f"""
📝 *New AI Task Created!*
*Task:* {task['task']}
*Assignee:* {task['assignee']}
*Due:* {task['due']}
🔗 *Jira:* <{jira_link}|{issue_key}>
"""
                    send_slack_message(slack_message)
                else:
                    # Task without Jira link
                    task_with_link = {**task, "jira_key": None, "jira_link": None}
                    processed_tasks.append(task_with_link)
                    
            except Exception as e:
                print(f"Error processing task {task['task']}: {e}")
                # Add task without Jira integration
                task_with_link = {**task, "jira_key": None, "jira_link": None}
                processed_tasks.append(task_with_link)
        
        # Update Confluence page with results
        confluence_page_id = request.confluence_page_id
        confluence_space_key = request.confluence_space_key or space_key
        
        if confluence_page_id:
            try:
                # Get next version number
                auth = base64.b64encode(f"{os.getenv('CONFLUENCE_USER_EMAIL')}:{os.getenv('CONFLUENCE_API_KEY')}".encode()).decode()
                res = requests.get(
                    f"{os.getenv('CONFLUENCE_BASE_URL')}/rest/api/content/{confluence_page_id}",
                    headers={"Authorization": f"Basic {auth}"}
                )
                next_version = 1
                if res.status_code == 200:
                    next_version = res.json()["version"]["number"] + 1
                
                # Create HTML table
                table_html = "<table><tr><th>Task</th><th>Assignee</th><th>Due</th><th>Jira</th></tr>"
                for task in processed_tasks:
                    link_html = f"<a href='{task.get('jira_link', '#')}' target='_blank'>View</a>" if task.get('jira_link') else "—"
                    table_html += f"<tr><td>{task['task']}</td><td>{task['assignee']}</td><td>{task['due']}</td><td>{link_html}</td></tr>"
                table_html += "</table>"
                
                # Update Confluence page
                headers = {
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "version": {"number": next_version},
                    "title": f"Action Items - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "type": "page",
                    "body": {
                        "storage": {
                            "value": table_html,
                            "representation": "storage"
                        }
                    }
                }
                
                response = requests.put(
                    f"{os.getenv('CONFLUENCE_BASE_URL')}/rest/api/content/{confluence_page_id}",
                    headers=headers,
                    json=payload
                )
                
                confluence_updated = response.status_code == 200
                
            except Exception as e:
                print(f"Error updating Confluence: {e}")
                confluence_updated = False
        else:
            confluence_updated = False
        
        return {
            "tasks": processed_tasks,
            "total_tasks": len(processed_tasks),
            "jira_issues_created": len([t for t in processed_tasks if t.get('jira_key')]),
            "confluence_updated": confluence_updated,
            "slack_notifications_sent": len(processed_tasks),
            "page_title": request.page_title,
            "space_key": space_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract meeting notes: {str(e)}")

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify backend is working"""
    return {"message": "Backend is working", "status": "ok"}

def get_actual_api_key_from_identifier(identifier: str) -> str:
    if identifier and identifier.startswith('GENAI_API_KEY_'):
        key = os.getenv(identifier)
        print(f"Using API key identifier: {identifier}, value: {key}")  # This will appear in Render logs
        if key:
            return key
    fallback = os.getenv('GENAI_API_KEY_1')
    print(f"Falling back to GENAI_API_KEY_1, value: {fallback}")
    return fallback

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

