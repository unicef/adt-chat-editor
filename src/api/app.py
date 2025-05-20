from dotenv import load_dotenv
from fastapi import FastAPI

from src.structs import ChatRequest
from src.workflows.graph import graph  # noqa: E402


load_dotenv()

# Create the FastAPI app
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    result = await graph.ainvoke(request)
    return {"result": result}
