from flask import Flask, render_template, request, jsonify
import io
import base64
import os
import traceback
import PyPDF2
import anthropic

app = Flask(__name__, template_folder='../templates')

# Debug mode - set to True to see full error traces
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Store summaries in memory (session-based storage would be better for production)
summaries_store = {}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes without writing to disk."""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def call_anthropic_api(system_prompt: str, user_message: str, api_key: str, api_base: str, model: str) -> str:
    """Call Anthropic API for summarization."""
    import httpx

    # Build client kwargs
    client_kwargs = {'api_key': api_key}

    # Only set base_url if it's provided and not the default Anthropic URL
    if api_base and api_base.strip() and api_base != 'https://api.anthropic.com':
        client_kwargs['base_url'] = api_base

    # Create httpx client with explicit configuration
    # Set trust_env=False to prevent environment proxy variables from interfering
    http_client = httpx.Client(
        timeout=300.0,  # 5 minute timeout for large PDFs
        follow_redirects=True,
        trust_env=False  # Don't use environment variables for proxies
    )
    client_kwargs['http_client'] = http_client

    client = anthropic.Anthropic(**client_kwargs)

    message = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    return message.content[0].text

def get_individual_summary_prompt() -> str:
    """Get the prompt for individual PDF summarization."""
    return """Create a concise, token-efficient markdown summary of this course material.

CRITICAL: Be CONCISE. Extract only essential information - this is an intermediate step.

Include:
- Key concepts & definitions (brief)
- Important formulas/equations (compact notation)
- Main frameworks/methodologies (bullet points)
- Critical distinctions/comparisons (tables if needed)
- Facts to memorize (lists)

Exclude:
- Verbose explanations
- Examples (unless essential for understanding)
- Redundant information
- Introductory/concluding fluff

Format: Use markdown with ##headers, bullets, **bold** for key terms, and tables for comparisons."""

def get_memorize_prompt(max_pages: int = None) -> str:
    """Get the memorization-focused LaTeX prompt."""
    return r"""Transform these course summaries into a memorization-focused LaTeX study guide.

OUTPUT REQUIREMENTS:
- Complete, compilable LaTeX document starting with \documentclass
- Use proper LaTeX packages: tikz, booktabs, xcolor, geometry, multicol
- All diagrams MUST be proper TikZ code (NO ASCII art, NO text diagrams)
- Tables use booktabs package (\toprule, \midrule, \bottomrule)
- Use \colorbox{yellow!30}{text} for highlights, \textcolor{red}{text} for warnings

DOCUMENT STRUCTURE:

\section{Mnemonics \& Memory Aids}
- Create a booktabs table with columns: Acronym | Stands For | Concept
- If no mnemonics exist, CREATE memorable ones for key lists
- Add quick recall phrases in bullet points

\section{Core Concepts Deep Dive}
- Identify the ONE most important concept
- Use booktabs tables for comparisons/distinctions
- Include detection methods if applicable
- Use \textbf{} for key terms

\section{Trade-offs \& Decision Making}
For each major technique/approach:
- Create booktabs tables with columns: Approach | Gains | Loses | When to Use
- Group by category (e.g., \subsection{Optimization Techniques})

\section{Decision Trees}
- Create 2-4 TikZ flowcharts using tikzpicture environment
- Use proper TikZ nodes: diamond shape for decisions, rectangle for actions
- Include arrows with labels (Yes/No)
- Example structure:
\begin{tikzpicture}[node distance=2cm]
\node[diamond] (q1) {Question?};
\node[rectangle, below left of=q1] (a1) {Action 1};
\node[rectangle, below right of=q1] (a2) {Action 2};
\draw[->] (q1) -- node[left] {Yes} (a1);
\draw[->] (q1) -- node[right] {No} (a2);
\end{tikzpicture}

\section{Quick Reference Tables}
- "If X → Use Y" decision table using booktabs
- Comparison tables for similar frameworks/concepts

\section{Common Exam Traps}
- Booktabs table: Statement | True/False | Why
- Use \textcolor{green}{✓} and \textcolor{red}{✗} for visual clarity
- Add memorable mantras

\section{Self-Test Checklist}
- Numbered list of 10-15 questions
- Brief answers in \textit{italics}

LATEX FORMATTING RULES:
- 11pt font, readable margins
- Use \colorbox{yellow!30}{} for definitions
- Use \colorbox{red!20}{} for warnings/traps
- NO ASCII art diagrams - only TikZ
- NO plain text tables - only booktabs
- Include all necessary \usepackage{} declarations

Here are the course summaries to transform:"""

def get_exam_notes_prompt(max_pages: int = 2) -> str:
    """Get the exam-focused concise notes prompt with page limit."""
    return fr"""Transform these course summaries into ultra-concise exam prep notes as a LaTeX PDF.

CRITICAL CONSTRAINT: MAXIMUM {max_pages} page(s). Every word must earn its place.

OUTPUT REQUIREMENTS:
- Complete, compilable LaTeX document starting with \documentclass{{article}}
- Use: geometry (small margins), multicol, booktabs, xcolor, enumitem
- 9pt or 10pt font, compact spacing
- Two-column layout where possible: \begin{{multicols}}{{2}}...\end{{multicols}}

REQUIRED PACKAGES IN PREAMBLE:
\usepackage[margin=1.2cm]{{geometry}}
\usepackage{{multicol}}
\usepackage{{booktabs}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\setlist{{nosep}}

DOCUMENT STRUCTURE:

\section*{{Key Formulas \& Definitions}}
- Booktabs table: Concept | Formula/Definition
- ONLY exam-critical items
- Use math mode: $...$

\section*{{Critical Concepts}}
- Brief itemized list using \begin{{itemize}}[noitemsep]
- One sentence per concept
- Highlight key terms: \textbf{{}}, \colorbox{{yellow!20}}{{}}

\section*{{Quick Decision Reference}}
- Booktabs table: "If X..." | "Then use Y" | "Why"
- Maximum information density

\section*{{Common Traps}}
- Compact itemized list
- Pattern: \textcolor{{red}}{{\textbf{{TRAP:}}}} Description → \textcolor{{green}}{{\textbf{{CORRECT:}}}} Fix
- One line per trap

\section*{{Mnemonics \& Memory Aids}}
- Bullet list of mnemonics (CREATE them if needed)
- Critical numbers/thresholds
- Quick recall phrases

LATEX FORMATTING RULES:
- NO ASCII art or text diagrams
- Use booktabs for ALL tables (\toprule, \midrule, \bottomrule)
- NO TikZ diagrams (too much space for {max_pages} page limit)
- Tight spacing: \setlength{{\parskip}}{{0pt}}
- Use \small or \footnotesize if needed to fit content
- Multi-column layout for lists when possible

RUTHLESS EXCLUSIONS:
- NO examples (unless absolutely essential)
- NO explanations longer than one sentence
- NO derivations
- NO background theory
- NO redundant information

The goal: Maximum exam-relevant information in {max_pages} page(s). Here are the summaries:"""

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
        if DEBUG:
            # Re-raise to see full traceback in debug mode
            raise
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if DEBUG else None
        }), 500

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
        if DEBUG:
            # Re-raise to see full traceback in debug mode
            raise
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if DEBUG else None
        }), 500

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
        if DEBUG:
            # Re-raise to see full traceback in debug mode
            raise
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if DEBUG else None
        }), 500

@app.route('/api/condense-summaries', methods=['POST'])
def condense_summaries():
    """Condense all summaries to make them more token-efficient."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        api_key = data.get('api_key')
        api_base = data.get('api_base', 'https://api.anthropic.com')
        model = data.get('model', 'claude-sonnet-4-5')

        if not api_key:
            return jsonify({'error': 'Missing API key'}), 400

        all_summaries = summaries_store.get(session_id, [])

        if not all_summaries:
            return jsonify({'error': 'No summaries to condense'}), 400

        # Condense each summary
        condensed_summaries = []
        for item in all_summaries:
            system_prompt = """You are condensing course summaries to reduce token count while preserving ALL essential information.

TASK: Make this summary MORE CONCISE while keeping:
- All key concepts, definitions, formulas
- All important distinctions and comparisons
- All facts that need to be memorized

Make it shorter by:
- Removing redundancy
- Using more compact notation
- Eliminating verbose explanations
- Using tables instead of paragraphs where possible
- Using abbreviations consistently

Output the condensed summary in markdown."""

            user_message = f"Original summary:\n\n{item['summary']}"

            condensed = call_anthropic_api(system_prompt, user_message, api_key, api_base, model)

            condensed_summaries.append({
                'filename': item['filename'],
                'summary': condensed
            })

        # Replace the summaries
        summaries_store[session_id] = condensed_summaries

        return jsonify({
            'success': True,
            'message': f'Condensed {len(condensed_summaries)} summaries'
        })

    except Exception as e:
        if DEBUG:
            # Re-raise to see full traceback in debug mode
            raise
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if DEBUG else None
        }), 500

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
        if DEBUG:
            # Re-raise to see full traceback in debug mode
            raise
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if DEBUG else None
        }), 500

# Enable Flask debug mode if DEBUG is True
if DEBUG:
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True

# Vercel serverless function handler
handler = app

# For local development
if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)
