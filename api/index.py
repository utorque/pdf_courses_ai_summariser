from flask import Flask, render_template, request, jsonify
import io
import base64
import PyPDF2
import anthropic

app = Flask(__name__, template_folder='../templates')

# Store summaries in memory (session-based storage would be better for production)
summaries_store = {}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes without writing to disk."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def call_anthropic_api(system_prompt: str, user_message: str, api_key: str, api_base: str, model: str) -> str:
    """Call Anthropic API for summarization."""
    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=api_base if api_base else None
        )

        message = client.messages.create(
            model=model,
            max_tokens=16000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return message.content[0].text
    except Exception as e:
        raise Exception(f"Error calling API: {str(e)}")

def get_individual_summary_prompt() -> str:
    """Get the prompt for individual PDF summarization."""
    return """You are an expert at creating detailed, structured summaries of course materials.

Your task is to analyze the provided PDF content and create a comprehensive markdown summary that:
1. Captures all key concepts, definitions, and important information
2. Maintains clear structure with headings and subheadings
3. Includes important examples, formulas, or diagrams mentioned
4. Preserves technical accuracy
5. Uses bullet points and lists for clarity

The summary should be thorough enough that someone could study from it without the original PDF."""

def get_memorize_prompt(max_pages: int = None) -> str:
    """Get the memorization-focused LaTeX prompt."""
    with open('prompt_memorise_pdf.md', 'r') as f:
        content = f.read()

    # Extract the template part
    template_start = content.find("I have course notes for")
    template_end = content.find("```", template_start + 10)
    base_prompt = content[template_start:template_end].strip()

    # Clean it up
    base_prompt = base_prompt.replace("[COURSE NAME]", "the provided course")
    base_prompt = base_prompt.replace("[DOMAIN]", "the subject domain")
    base_prompt = base_prompt.replace("[ROLE]", "a student")
    base_prompt = base_prompt.replace("[PASTE NOTES HERE]", "")

    return base_prompt

def get_exam_notes_prompt(max_pages: int = 2) -> str:
    """Get the exam-focused concise notes prompt with page limit."""
    return f"""I have course summaries that I need to transform into concise exam preparation notes as a LaTeX PDF.

CRITICAL CONSTRAINT: The final document must be MAXIMUM {max_pages} page(s). Be extremely selective and concise.

Please create a document with the following structure:

## 1. KEY FORMULAS & DEFINITIONS
A compact table with only the most essential formulas and definitions that will be tested.

## 2. CRITICAL CONCEPTS CHEAT SHEET
One paragraph per major concept - just enough to trigger memory recall. Focus on:
- What distinguishes this from similar concepts
- When/why to use it
- Common mistakes to avoid

## 3. QUICK DECISION TABLE
"If X situation → Use Y approach" table for rapid exam lookup.

## 4. EXAM TRAPS & GOTCHAS
Bullet list of common mistakes and misconceptions with brief explanations.

## 5. MEMORIZATION AIDS
- Key mnemonics (create them if needed)
- Quick recall phrases
- Important numbers/thresholds to remember

## Style requirements:
- COMPACT: Use small margins, 10pt font, multi-column layout where possible
- Tables with booktabs for clean look
- Color highlighting for critical terms (yellow for definitions, red for warnings)
- NO unnecessary whitespace
- NO lengthy explanations - just what's needed for exam recall

## DO NOT include:
- Examples (unless absolutely critical for understanding)
- Background theory
- Anything obvious or already known
- Derivations or proofs

The goal is MAXIMUM information density for exam day. Here are the course summaries:"""

def compile_latex_to_pdf(latex_content: str) -> bytes:
    """
    Try to compile LaTeX to PDF. For Vercel, we'll use a cloud compilation service.
    If that fails, we'll return the LaTeX source for manual compilation.
    """
    try:
        import requests

        # Use latex.online service (no API key needed)
        url = "https://latexonline.cc/compile"
        params = {
            'text': latex_content,
            'command': 'pdflatex'
        }

        response = requests.get(url, params=params, timeout=90)

        if response.status_code == 200:
            return response.content
        else:
            # Fallback: return None to indicate compilation not available
            return None
    except Exception as e:
        # Fallback: return None to indicate compilation not available
        return None

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/summarize-pdf', methods=['POST'])
def summarize_pdf():
    """Summarize a single PDF."""
    try:
        data = request.json
        pdf_base64 = data.get('pdf_content')
        filename = data.get('filename')
        user_context = data.get('user_context', '')
        api_key = data.get('api_key')
        api_base = data.get('api_base', 'https://api.anthropic.com')
        model = data.get('model', 'claude-sonnet-4-5')
        session_id = data.get('session_id', 'default')

        if not pdf_base64 or not api_key:
            return jsonify({'error': 'Missing PDF content or API key'}), 400

        # Decode PDF
        pdf_bytes = base64.b64decode(pdf_base64)

        # Extract text
        pdf_text = extract_text_from_pdf(pdf_bytes)

        # Build user message
        user_message = f"PDF Filename: {filename}\n\n"
        if user_context:
            user_message += f"User Requirements:\n{user_context}\n\n"
        user_message += f"PDF Content:\n{pdf_text}"

        # Get summary
        system_prompt = get_individual_summary_prompt()
        summary = call_anthropic_api(system_prompt, user_message, api_key, api_base, model)

        # Store in memory
        if session_id not in summaries_store:
            summaries_store[session_id] = []

        summaries_store[session_id].append({
            'filename': filename,
            'summary': summary
        })

        return jsonify({
            'success': True,
            'summary': summary,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-final-pdf', methods=['POST'])
def generate_final_pdf():
    """Generate final LaTeX PDF from all summaries."""
    try:
        data = request.json
        pdf_type = data.get('type', 'memorize')  # 'memorize' or 'exam'
        max_pages = data.get('max_pages', 2)
        user_context = data.get('user_context', '')
        user_summaries = data.get('user_summaries', '')
        api_key = data.get('api_key')
        api_base = data.get('api_base', 'https://api.anthropic.com')
        model = data.get('model', 'claude-sonnet-4-5')
        session_id = data.get('session_id', 'default')

        if not api_key:
            return jsonify({'error': 'Missing API key'}), 400

        # Get all summaries
        all_summaries = summaries_store.get(session_id, [])

        if not all_summaries and not user_summaries:
            return jsonify({'error': 'No summaries available'}), 400

        # Build combined content
        combined_content = ""

        if user_summaries:
            combined_content += "## User-Provided Summaries\n\n" + user_summaries + "\n\n"

        for item in all_summaries:
            combined_content += f"## {item['filename']}\n\n{item['summary']}\n\n"

        # Get appropriate prompt
        if pdf_type == 'exam':
            system_prompt = get_exam_notes_prompt(max_pages)
        else:
            system_prompt = get_memorize_prompt()

        # Build user message
        user_message = ""
        if user_context:
            user_message += f"Additional Context/Requirements:\n{user_context}\n\n"
        user_message += combined_content

        # Generate LaTeX
        latex_content = call_anthropic_api(system_prompt, user_message, api_key, api_base, model)

        # Extract LaTeX code if wrapped in markdown
        if '```latex' in latex_content:
            start = latex_content.find('```latex') + 8
            end = latex_content.find('```', start)
            latex_content = latex_content[start:end].strip()
        elif '```' in latex_content:
            start = latex_content.find('```') + 3
            end = latex_content.find('```', start)
            latex_content = latex_content[start:end].strip()

        # Try to compile to PDF
        pdf_bytes = compile_latex_to_pdf(latex_content)

        if pdf_bytes:
            # Return PDF as base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return jsonify({
                'success': True,
                'pdf': pdf_base64,
                'latex': latex_content,
                'filename': f"{pdf_type}_notes.pdf",
                'has_pdf': True
            })
        else:
            # Return LaTeX source only
            return jsonify({
                'success': True,
                'latex': latex_content,
                'filename': f"{pdf_type}_notes.tex",
                'has_pdf': False
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-summaries', methods=['POST'])
def download_summaries():
    """Download all summaries as a single markdown file."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')

        all_summaries = summaries_store.get(session_id, [])

        if not all_summaries:
            return jsonify({'error': 'No summaries available'}), 400

        # Build markdown content
        markdown_content = "# Course Summaries\n\n"
        for item in all_summaries:
            markdown_content += f"## {item['filename']}\n\n{item['summary']}\n\n---\n\n"

        # Return as base64
        markdown_base64 = base64.b64encode(markdown_content.encode()).decode('utf-8')

        return jsonify({
            'success': True,
            'content': markdown_base64,
            'filename': 'all_summaries.md'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-summaries', methods=['POST'])
def clear_summaries():
    """Clear all summaries for a session."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')

        if session_id in summaries_store:
            del summaries_store[session_id]

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel serverless function handler
app = app
