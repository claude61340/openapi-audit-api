from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="OpenAPI Audit API",
    version="1.0.0"
)

class ValidationRequest(BaseModel):
    specification: str

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "OpenAPI Audit API"
    }

@app.post("/validate")
def validate_openapi(request: ValidationRequest):
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "message": "Endpoint de validation opérationnel. Le validateur OpenAPI réel sera ajouté ensuite."
    }
