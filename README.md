# YoutubeChatBot

Quick local runner for a YouTube transcript + RAG demo using Google Generative AI.

Requirements

- Python 3.10+
- See `requirements.txt` for packages to install.

Setup

1. Create a virtual environment and activate it.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Add environment variables in a `.env` file at project root:

```
GOOGLE_API_KEY=your_api_key_here
```

Usage

- Run the transcript-based QA demo:

```powershell
python main.py
```

Enter a YouTube video ID when prompted and ask a question about the transcript.

Files

- `main.py`: Transcript fetch -> chunk -> FAISS -> RAG with Google Generative AI.
- `main1(scores).py`, `main2(chaining).py`, `main3(chromavs).py`: experimental scripts referenced in the project.

Notes

- You may need to adjust dependency names depending on available packages in PyPI for Google Generative AI integrations.

# YoutubeChatBot
