# 📚 PDF Course Summarizer with AI

A Flask web application that uses Claude AI to automatically summarize course PDFs and generate LaTeX-formatted study materials. Optimized for deployment on Vercel.

## Features

- 📄 **Multi-PDF Upload**: Upload multiple course PDFs at once
- 🤖 **AI-Powered Summaries**: Uses Claude Sonnet 4.5 to generate detailed summaries for each PDF
- 📝 **Custom Context**: Add your own requirements and context for tailored summaries
- 💾 **Flexible Export Options**:
  - Download individual summaries as markdown
  - Generate memorization-focused LaTeX study guides
  - Generate concise exam notes with configurable page limits (1-N pages)
- 🎯 **Two Summary Types**:
  - **Memorize PDF**: Comprehensive study guide with mnemonics, decision trees, and deep dives
  - **Exam Notes**: Ultra-concise notes optimized for exam preparation with configurable page limit
- 🔧 **API Flexible**: Works with Anthropic API or any OpenAI-compatible endpoint

## User Story

1. Upload your course PDFs
2. (Optional) Paste any existing summaries you have
3. Add custom context about what you need in the summaries
4. Click "Start One-by-One Summary" to process each PDF
5. Download all summaries as markdown, or:
6. Generate a "Memorize PDF" for comprehensive learning
7. Generate "Exam Notes" with a specific page limit (default: 2 pages)

## Deployment on Vercel

### Prerequisites

- A [Vercel account](https://vercel.com)
- An [Anthropic API key](https://console.anthropic.com/)

### Deploy Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pdf_courses_ai_summariser.git
   cd pdf_courses_ai_summariser
   ```

2. Install Vercel CLI (optional):
   ```bash
   npm i -g vercel
   ```

3. Deploy to Vercel:
   ```bash
   vercel
   ```

   Or use the Vercel Dashboard:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your Git repository
   - Vercel will auto-detect the configuration
   - Click "Deploy"

### Environment Variables

The application doesn't require server-side environment variables - users enter their API keys directly in the UI for maximum flexibility.

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask app:
   ```bash
   python -m flask --app api/index run
   ```

3. Open your browser to `http://localhost:5000`

## How to Use

### 1. API Configuration

Enter your API credentials:
- **API Key**: Your Anthropic API key (required)
- **API Base URL**: Default is `https://api.anthropic.com` (change if using a proxy)
- **Model**: Default is `claude-sonnet-4-5`

### 2. Upload PDFs

- Click the upload area or drag & drop PDF files
- Multiple files are supported
- Each file will be processed individually

### 3. Add Context

- **User Summaries**: Paste any existing markdown summaries you have
- **Additional Context**: Specify what you need or don't need in the summaries
  - Example: "I'm a CS student, skip basic programming. Focus on algorithms."

### 4. Generate Summaries

Click "Start One-by-One Summary" to process each PDF sequentially. Progress is shown with a progress bar.

### 5. Download Options

- **Download All Summaries**: Get all summaries as a single markdown file
- **Generate & Download Memorize PDF**: Creates a comprehensive LaTeX study guide
- **Generate & Download Exam Notes**: Creates ultra-concise exam prep notes (adjustable page limit)

## Technical Details

### Architecture

- **Frontend**: Pure HTML/CSS/JavaScript (no build step required)
- **Backend**: Flask (Python)
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **PDF Processing**: PyPDF2 for text extraction
- **LaTeX Compilation**: Cloud-based compilation via latexonline.cc

### File Structure

```
pdf_courses_ai_summariser/
├── api/
│   └── index.py              # Flask application
├── templates/
│   └── index.html            # Frontend UI
├── prompt_memorise_pdf.md    # Memorization prompt template
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
└── README.md                # This file
```

### API Endpoints

- `GET /` - Main application page
- `POST /api/summarize-pdf` - Summarize a single PDF
- `POST /api/generate-final-pdf` - Generate final LaTeX document
- `POST /api/download-summaries` - Download all summaries as markdown
- `POST /api/clear-summaries` - Clear session summaries

## Prompts

### Individual PDF Summary Prompt

Each PDF is summarized with a comprehensive prompt that:
- Captures all key concepts and definitions
- Maintains clear structure
- Includes examples and formulas
- Preserves technical accuracy

### Memorize PDF Prompt

Based on `prompt_memorise_pdf.md`, includes:
- Mnemonics table
- Quick recall phrases
- Core concept deep dives
- Trade-offs sections
- Decision trees (TikZ)
- Exam traps and self-test checklists

### Exam Notes Prompt

Optimized for brevity and density:
- Key formulas & definitions
- Critical concepts cheat sheet
- Quick decision tables
- Exam traps & gotchas
- Memorization aids
- Configurable page limit (1-N pages)

## Limitations

- LaTeX compilation happens via a free online service (latexonline.cc)
  - If compilation fails, you'll receive the `.tex` source file
  - Upload to [Overleaf](https://overleaf.com) or compile locally
- Vercel has a 10-second timeout for serverless functions
  - Very large PDFs may timeout
  - Solution: Use smaller chunks or deploy on a traditional server
- Summaries are stored in memory (not persistent)
  - Summaries are lost when the server restarts
  - For production, consider using Redis or a database

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - feel free to use this project for your own courses!

## Credits

Built with:
- [Flask](https://flask.palletsprojects.com/)
- [Anthropic Claude API](https://www.anthropic.com/)
- [PyPDF2](https://pypdf2.readthedocs.io/)
- [Vercel](https://vercel.com/)

## Support

For issues or questions, please open a GitHub issue.