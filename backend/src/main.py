from fastapi import FastAPI

app = FastAPI(
    title="Local RAG Comparator API",
    description="Vector RAG vs GraphRAG 比較検証 API",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
