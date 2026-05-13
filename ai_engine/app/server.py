from fastapi import FastAPI
from langserve import add_routes
from app.graph.builder import get_chat_graph
import os
import httpx

app = FastAPI(
    title="ModAI Orchestrator",
    version="1.0",
    description="Serviço LangServe isolado para execução de IA",
)

# Enable CORS if needed
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

graph = get_chat_graph()

# Create LangServe route
add_routes(
    app,
    graph,
    path="/chat",
)

from app.graph.llm import get_fast_model
from pydantic import BaseModel

class SummarizeRequest(BaseModel):
    prompt: str

@app.post("/internal/summarize")
async def summarize(req: SummarizeRequest):
    try:
        model = get_fast_model()
        resp = await model.ainvoke(req.prompt)
        return {"summary": resp.content.strip()}
    except Exception as e:
        return {"summary": "", "error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}
