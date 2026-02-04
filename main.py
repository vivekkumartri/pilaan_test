from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os
from pymongo import MongoClient
from pathlib import Path

# ---------------- CONFIG ----------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personality Assessment (Monolith)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static folder
STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# MongoDB
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set")

client = MongoClient(MONGO_URI)

try:
    logger.info(client.list_database_names())
except Exception as e:
    logger.error("Mongo connection failed: %s", e)

db = client["pilaan"]
collection = db["user"]

# ---------------- MODELS ----------------

class CursorMovement(BaseModel):
    x: int
    y: int
    timestamp: int

class CursorData(BaseModel):
    movements: List[CursorMovement]
    total_movements: int
    first_movement: Optional[CursorMovement] = None
    last_movement: Optional[CursorMovement] = None

class ResponseTiming(BaseModel):
    response_time_ms: int
    response_time_seconds: str
    selected_option: str
    timestamp: str

class Analytics(BaseModel):
    total_time_ms: int
    total_time_seconds: str
    total_time_minutes: str
    average_time_per_question_seconds: str
    total_cursor_movements: int

class AssessmentSubmission(BaseModel):
    user_name: str
    email_id: EmailStr
    phone_number: str
    responses: Dict[str, str]
    response_timings: Dict[str, ResponseTiming]
    cursor_movements: Dict[str, CursorData]
    total_questions: int
    analytics: Analytics

class AssessmentResponse(BaseModel):
    success: bool
    message: str
    data: Dict

# ---------------- HELPERS ----------------

def generate_user_id(name: str, phone: str) -> str:
    return f"{name.replace(' ', '_').lower()}_{phone}"

def calculate_cursor_stats(cursor_movements: Dict[str, CursorData]) -> Dict[str, Any]:
    stats = {
        "total_questions_tracked": len(cursor_movements),
        "total_movements_all_questions": 0,
        "average_movements_per_question": 0,
        "questions_with_most_movement": None,
        "questions_with_least_movement": None,
        "movement_details": {}
    }

    if not cursor_movements:
        return stats

    movement_counts = {}
    total_movements = 0

    for qid, data in cursor_movements.items():
        count = data.total_movements
        movement_counts[qid] = count
        total_movements += count

        if len(data.movements) > 1:
            dist = 0
            for i in range(1, len(data.movements)):
                p, c = data.movements[i-1], data.movements[i]
                d = ((c.x - p.x)**2 + (c.y - p.y)**2)**0.5
                dist += d

            stats["movement_details"][qid] = {
                "total_movements": count,
                "total_distance_pixels": round(dist, 2),
                "average_distance_per_movement": round(dist/count, 2) if count > 0 else 0
            }

    stats["total_movements_all_questions"] = total_movements
    stats["average_movements_per_question"] = round(
        total_movements / len(cursor_movements), 2
    )

    stats["questions_with_most_movement"] = max(movement_counts, key=movement_counts.get)
    stats["questions_with_least_movement"] = min(movement_counts, key=movement_counts.get)

    return stats

# ---------------- ROUTES ----------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return HTMLResponse(
        STATIC_DIR.joinpath("index.html").read_text(encoding="utf-8")
    )

@app.post("/api/submit", response_model=AssessmentResponse)
async def submit_assessment(submission: AssessmentSubmission):
    try:
        user_id = generate_user_id(
            submission.user_name,
            submission.phone_number
        )
        timestamp = datetime.now().isoformat()
        cursor_stats = calculate_cursor_stats(
            submission.cursor_movements
        )

        assessment_data = {
            "user_id": user_id,
            "user_name": submission.user_name,
            "email_id": submission.email_id,
            "phone_number": submission.phone_number,
            "timestamp": timestamp,
            "responses": submission.responses,
            "response_timings": {
                k: v.dict() for k, v in submission.response_timings.items()
            },
            "cursor_movements": {
                k: v.dict() for k, v in submission.cursor_movements.items()
            },
            "total_questions": submission.total_questions,
            "answered_questions": len(submission.responses),
            "analytics": submission.analytics.dict(),
            "cursor_statistics": cursor_stats
        }

        result = collection.insert_one(assessment_data)

        # 🔥 FIX: Convert ObjectId to string
        assessment_data["_id"] = str(result.inserted_id)

        return AssessmentResponse(
            success=True,
            message="Saved successfully",
            data=assessment_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assessments")
async def list_all():
    data = list(collection.find({}))
    for d in data:
        d["_id"] = str(d["_id"])  # 🔥 FIX
    return {
        "count": len(data),
        "assessments": data
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "records": collection.count_documents({})
    }

# ---------------- RUN ----------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )
