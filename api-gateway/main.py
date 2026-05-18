from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

class ChatRequest(BaseModel):
    query: str
    embedding: list[float] = Field(default_factory=lambda: [0.0] * 384)

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

@app.post("/api/v1/chat")
async def chat(body: ChatRequest):
    query = body.query
    start = time.time()

    async with httpx.AsyncClient() as client:
        search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
            "vector": body.embedding,
            "limit": 3
        })
        context = search_resp.json().get("result", [])

    prompt = f"Context: {context}\n\nQuery: {query}"
    async with httpx.AsyncClient(timeout=30) as client:
        llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
            "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
            "messages": [{"role": "user", "content": prompt}]
        })

    latency = (time.time() - start) * 1000
    result = llm_resp.json()

    return {
        "answer": result["choices"][0]["message"]["content"],
        "latency_ms": round(latency, 2),
        "model": result["model"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}
