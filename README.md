# PA Call Center Agent

A LangGraph-based chatbot agent simulating a prior authorization call center workflow.

## Setup

1. **Install Dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```
   Or install requirements manually.

2. **Environment Variables**:
   Copy `.env` and fill in your keys:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

## Running the Agent

### Command Line
To visualize the graph:
```bash
python -m app.main
```

### LangSmith Studio (LangGraph Dev)
To run the development server and interact via LangSmith Studio (supports streaming):
```bash
langgraph dev
```
Wait for the output `API: http://127.0.0.1:2024` and then open the provided Studio link.

### Streamlit App
To run the interactive chat interface:
```bash
streamlit run streamlit_app.py
```

## Structure
- `app/graph.py`: The core LangGraph definition.
- `app/nodes/`: Individual workflow nodes.
- `prompts/`: Jinja2 templates for prompts.
- `data/`: Mock database.
