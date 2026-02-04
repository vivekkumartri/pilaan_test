from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personality Assessment API with Tracking")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for data storage
DATA_DIR = Path("assessment_data")
DATA_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
# Pydantic models for request/response
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

# Helper function to generate user ID
def generate_user_id(name: str, phone: str) -> str:
    """Generate a unique user ID from name and phone"""
    clean_name = name.replace(" ", "_").lower()
    return f"{clean_name}_{phone}"

# Helper function to calculate cursor statistics
def calculate_cursor_stats(cursor_movements: Dict[str, CursorData]) -> Dict[str, Any]:
    """Calculate detailed cursor movement statistics"""
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
    
    for question_id, cursor_data in cursor_movements.items():
        count = cursor_data.total_movements
        movement_counts[question_id] = count
        total_movements += count
        
        # Calculate distance traveled if there are movements
        if cursor_data.movements and len(cursor_data.movements) > 1:
            total_distance = 0
            for i in range(1, len(cursor_data.movements)):
                prev = cursor_data.movements[i-1]
                curr = cursor_data.movements[i]
                distance = ((curr.x - prev.x)**2 + (curr.y - prev.y)**2)**0.5
                total_distance += distance
            
            stats["movement_details"][question_id] = {
                "total_movements": count,
                "total_distance_pixels": round(total_distance, 2),
                "average_distance_per_movement": round(total_distance / count, 2) if count > 0 else 0
            }
    
    stats["total_movements_all_questions"] = total_movements
    stats["average_movements_per_question"] = round(total_movements / len(cursor_movements), 2) if cursor_movements else 0
    
    if movement_counts:
        stats["questions_with_most_movement"] = max(movement_counts, key=movement_counts.get)
        stats["questions_with_least_movement"] = min(movement_counts, key=movement_counts.get)
    
    return stats

# Helper function to save assessment data
def save_assessment(data: dict) -> str:
    """Save assessment data to JSON file"""
    try:
        user_id = data["user_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}.json"
        filepath = DATA_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Assessment saved: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving assessment: {e}")
        raise

@app.get("/")
async def root():
    """Serve the main HTML page"""
    html_file = Path("personality_assessment_with_tracking.html")
    if html_file.exists():
        return FileResponse(html_file)
    return {"message": "Personality Assessment API with Tracking", "status": "running"}

@app.post("/api/submit", response_model=AssessmentResponse)
async def submit_assessment(submission: AssessmentSubmission):
    """
    Submit a personality assessment with response timings and cursor tracking
    
    - Validates the submission data
    - Generates a unique user ID
    - Calculates cursor movement statistics
    - Saves data to JSON file on server
    - Returns success response with saved data
    """
    try:
        # Generate user ID
        user_id = generate_user_id(submission.user_name, submission.phone_number)
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Calculate cursor statistics
        cursor_stats = calculate_cursor_stats(submission.cursor_movements)
        
        # Prepare data for storage
        assessment_data = {
            "user_id": user_id,
            "user_name": submission.user_name,
            "email_id": submission.email_id,
            "phone_number": submission.phone_number,
            "timestamp": timestamp,
            "responses": submission.responses,
            "response_timings": {k: v.dict() for k, v in submission.response_timings.items()},
            "cursor_movements": {k: v.dict() for k, v in submission.cursor_movements.items()},
            "total_questions": submission.total_questions,
            "answered_questions": len(submission.responses),
            "analytics": submission.analytics.dict(),
            "cursor_statistics": cursor_stats
        }
        
        # Save to file
        filepath = save_assessment(assessment_data)
        
        # Log the submission with tracking info
        logger.info(f"Assessment submitted by {submission.user_name} ({user_id})")
        logger.info(f"Email: {submission.email_id}, Phone: {submission.phone_number}")
        logger.info(f"Answered {len(submission.responses)}/{submission.total_questions} questions")
        logger.info(f"Total time: {submission.analytics.total_time_minutes} minutes")
        logger.info(f"Average time per question: {submission.analytics.average_time_per_question_seconds} seconds")
        logger.info(f"Total cursor movements: {submission.analytics.total_cursor_movements}")
        logger.info(f"Saved to: {filepath}")
        
        return AssessmentResponse(
            success=True,
            message="Assessment submitted successfully with tracking data",
            data=assessment_data
        )
        
    except Exception as e:
        logger.error(f"Error processing submission: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save assessment: {str(e)}"
        )

@app.get("/api/assessments")
async def list_assessments():
    """List all saved assessments (admin endpoint)"""
    try:
        assessments = []
        for file in DATA_DIR.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract summary info
                analytics = data.get("analytics", {})
                cursor_stats = data.get("cursor_statistics", {})
                
                assessments.append({
                    "filename": file.name,
                    "user_id": data.get("user_id"),
                    "user_name": data.get("user_name"),
                    "email_id": data.get("email_id"),
                    "timestamp": data.get("timestamp"),
                    "answered_questions": data.get("answered_questions"),
                    "total_questions": data.get("total_questions"),
                    "total_time_minutes": analytics.get("total_time_minutes"),
                    "average_time_per_question": analytics.get("average_time_per_question_seconds"),
                    "total_cursor_movements": cursor_stats.get("total_movements_all_questions", 0)
                })
        
        assessments.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"count": len(assessments), "assessments": assessments}
        
    except Exception as e:
        logger.error(f"Error listing assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assessment/{user_id}")
async def get_assessment(user_id: str):
    """Get a specific assessment by user_id (admin endpoint)"""
    try:
        # Find the most recent file for this user
        files = list(DATA_DIR.glob(f"{user_id}_*.json"))
        if not files:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Get the most recent file
        latest_file = sorted(files, reverse=True)[0]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{user_id}")
async def get_assessment_analytics(user_id: str):
    """Get detailed analytics for a specific assessment"""
    try:
        # Find the most recent file for this user
        files = list(DATA_DIR.glob(f"{user_id}_*.json"))
        if not files:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        latest_file = sorted(files, reverse=True)[0]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract analytics
        analytics = {
            "user_info": {
                "user_id": data.get("user_id"),
                "user_name": data.get("user_name"),
                "email_id": data.get("email_id"),
                "timestamp": data.get("timestamp")
            },
            "completion": {
                "total_questions": data.get("total_questions"),
                "answered_questions": data.get("answered_questions"),
                "completion_rate": f"{(data.get('answered_questions', 0) / data.get('total_questions', 1) * 100):.1f}%"
            },
            "timing": data.get("analytics", {}),
            "cursor_tracking": data.get("cursor_statistics", {}),
            "question_details": []
        }
        
        # Add per-question details
        response_timings = data.get("response_timings", {})
        cursor_movements = data.get("cursor_movements", {})
        
        for question_id in data.get("responses", {}).keys():
            question_detail = {
                "question_id": question_id,
                "selected_option": data["responses"][question_id],
            }
            
            if question_id in response_timings:
                question_detail["timing"] = response_timings[question_id]
            
            if question_id in cursor_movements:
                cursor_data = cursor_movements[question_id]
                question_detail["cursor_activity"] = {
                    "total_movements": cursor_data.get("total_movements", 0),
                    "has_movement_data": len(cursor_data.get("movements", [])) > 0
                }
            
            analytics["question_details"].append(question_detail)
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_directory": str(DATA_DIR),
        "total_assessments": len(list(DATA_DIR.glob("*.json"))),
        "features": ["response_timing", "cursor_tracking", "detailed_analytics"]
    }

# Mount static files if needed
if STATIC_DIR.exists():
    app.mount("/static/index.html", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Personality Assessment Server with Tracking")
    print("=" * 60)
    print(f"Data will be saved to: {DATA_DIR.absolute()}")
    print("Features enabled:")
    print("  ✓ Response timing tracking")
    print("  ✓ Cursor movement tracking")
    print("  ✓ Detailed analytics")
    print(f"Starting server on http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
