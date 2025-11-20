import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Lead as LeadSchema
from database import create_document, get_documents, db

app = FastAPI(title="Dot 2 Connect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    service_interest: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Dot 2 Connect backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/leads", response_model=dict)
def create_lead(lead: LeadSchema):
    try:
        inserted_id = create_document("lead", lead)
        return {"status": "success", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads", response_model=List[LeadResponse])
def list_leads(limit: int = Query(10, ge=1, le=100)):
    try:
        docs = get_documents("lead", {}, limit)
        # Convert ObjectId to string and map fields
        results: List[LeadResponse] = []
        for d in docs:
            results.append(LeadResponse(
                id=str(d.get("_id")),
                name=d.get("name", ""),
                email=d.get("email", ""),
                company=d.get("company"),
                phone=d.get("phone"),
                message=d.get("message"),
                service_interest=d.get("service_interest"),
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
