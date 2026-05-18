from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = None

class ChatCompletionResponseChoice(BaseModel):
    message: Message

class ChatCompletionResponse(BaseModel):
    choices: List[ChatCompletionResponseChoice]
    model: str

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    query = request.messages[-1].content if request.messages else ""
    content = f"Mocked response based on query: {query}"
    return ChatCompletionResponse(
        choices=[
            ChatCompletionResponseChoice(
                message=Message(role="assistant", content=content)
            )
        ],
        model="Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
    )

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    embeddings = [[0.1] * 384 for _ in request.texts]
    return EmbedResponse(embeddings=embeddings)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
