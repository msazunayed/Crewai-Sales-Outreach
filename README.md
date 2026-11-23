# CrewAI Sales Outreach

From lead discovery to personalized engagement. Two CrewAI agents research a lead and draft
personalized emails; a plain HTML/CSS/JS frontend (white and cream theme) drives them.

```
crewai-sales-outreach/
├── ai/                  CrewAI agents, tasks, tools + FastAPI server
│   ├── main.py          API (/api/run, /api/jobs/{id}) and static hosting for frontend
│   ├── crew.py          agents, tasks, crew
│   ├── tools.py         custom SentimentAnalysisTool
│   └── instructions/    guidelines the agents read
├── frontend/            index.html, style.css, app.js
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

## Environment Setup
```venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add OPENAI_API_KEY and SERPER_API_KEY
uvicorn main:app --app-dir ai --reload --port 8000
```

```conda
conda create --name <env_name>  python=<python_version>     # creates env "crewai-sales-outreach" (Python 3.11)
conda activate <env_name>
pip install -r requirements.txt  
cp .env.example .env                    # add OPENAI_API_KEY and SERPER_API_KEY
uvicorn main:app --app-dir ai --reload --port 8000
```
Open http://localhost:8000. The server also serves the `frontend/` folder.

Generated reports are saved to `ai/outputs/`. Edit `ai/instructions/*.md` to change agent guidelines.

## License
MIT, see [LICENSE](LICENSE).
