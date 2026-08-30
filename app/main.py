from fastapi import FastAPI

app = FastAPI(
    title="Text2SQL Workspace",
    description="Multi-user LLM Data Query Service",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "UP"}
