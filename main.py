import os
import logging
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel

# Import local modules
from database import init_db
from auth import signup, login, get_current_user, UserCreate
from response_generator import generate_response, ChatMessage
from knowledge_base import KnowledgeBase
from search_utils import search_documents
from classifier import load_model_and_tokenizer, predict_text
from content_processor import ContentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
knowledge_bases: Dict[str, KnowledgeBase] = {}
classification_model = None
tokenizer = None
content_processor = None

# Pydantic models
class VerificationRequest(BaseModel):
    content: str
    content_type: str  # "text", "url", "image_description", "video_description"
    session_id: str

class VerificationResponse(BaseModel):
    status: str
    summary: str
    classification_score: float
    classification_label: str
    credibility_assessment: str
    sources: List[Dict[str, str]]
    timestamp: datetime

class ChatRequest(BaseModel):
    query: str
    session_id: str

class RefreshKnowledgeBaseRequest(BaseModel):
    topic: str
    session_id: str

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    global classification_model, tokenizer, content_processor
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Load classification model and tokenizer
        model_path = os.getenv("MODEL_PATH", "models/classification_model.h5")
        tokenizer_path = os.getenv("TOKENIZER_PATH", "models/tokenizer.pkl")
        
        if os.path.exists(model_path) and os.path.exists(tokenizer_path):
            classification_model, tokenizer = load_model_and_tokenizer(model_path, tokenizer_path)
            logger.info("Classification model and tokenizer loaded successfully")
        else:
            logger.warning("Classification model or tokenizer not found. Text classification will be disabled.")
        
        # Initialize content processor
        content_processor = ContentProcessor()
        logger.info("Content processor initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Cleanup code here if needed
    logger.info("Application shutdown")

# Create FastAPI app
app = FastAPI(
    title="SCEPTRE API",
    description="Smart Cognitive Engine for Preventing Tricks, Rumors & Errors",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
@app.post("/signup")
async def register_user(user: UserCreate):
    """Register a new user."""
    return await signup(user)

@app.post("/login")
async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    return await login(form_data)

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """Protected route example."""
    return {"message": f"Hello {current_user['email']}, you are authenticated!"}

# Main verification endpoint
@app.post("/verify", response_model=VerificationResponse)
async def verify_content(
    content: Optional[str] = Form(None),
    session_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Main endpoint to verify content for misinformation.
    Accepts text, file upload, or URL.
    """
    try:
        if not content_processor:
            raise HTTPException(status_code=500, detail="Content processor not initialized")
        
        # Determine content type and process accordingly
        processed_content = None
        content_type = "text"
        
        if file:
            # Handle file upload (image or video)
            if file.content_type.startswith('image/'):
                content_type = "image"
                processed_content = await content_processor.process_image(file)
            elif file.content_type.startswith('video/'):
                content_type = "video"
                processed_content = await content_processor.process_video(file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        elif url:
            # Handle URL
            content_type = "url"
            processed_content = await content_processor.process_url(url)
        elif content:
            # Handle text content
            content_type = "text"
            processed_content = content
        else:
            raise HTTPException(status_code=400, detail="No content provided")
        
        if not processed_content:
            raise HTTPException(status_code=400, detail="Failed to process content")
        
        # Create verification request
        verification_request = VerificationRequest(
            content=processed_content,
            content_type=content_type,
            session_id=session_id
        )
        
        # Perform verification
        result = await perform_verification(verification_request)
        return result
        
    except Exception as e:
        logger.error(f"Error in verify_content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_verification(request: VerificationRequest) -> VerificationResponse:
    """Perform the complete verification workflow."""
    try:
        # Step 1: Classify the content using the ML model
        classification_score = 0.5
        classification_label = "neutral"
        
        if classification_model and tokenizer:
            try:
                classification_result = predict_text(request.content, classification_model, tokenizer)
                classification_score = classification_result["prediction"]
                classification_label = classification_result["label"]
                logger.info(f"Classification result: {classification_score} ({classification_label})")
            except Exception as e:
                logger.error(f"Error in classification: {e}")
        
        # Step 2: Search for verification information
        search_query = request.content[:200]  # Limit query length
        search_results = await search_documents(search_query)
        
        # Step 3: Update knowledge base with search results
        if request.session_id not in knowledge_bases:
            knowledge_bases[request.session_id] = KnowledgeBase(request.session_id)
        
        kb = knowledge_bases[request.session_id]
        kb.add_documents(search_results.results)
        
        # Step 4: Generate verification response
        chat_history = []
        verification_query = f"Analyze this content for misinformation: {request.content}"
        
        response_data = await generate_response(
            verification_query,
            chat_history,
            request.session_id,
            knowledge_bases
        )
        
        # Step 5: Determine credibility assessment
        credibility_assessment = determine_credibility(
            classification_score,
            len(search_results.results),
            response_data["answer"]
        )
        
        # Prepare sources
        sources = [
            {"title": doc.title, "url": doc.url, "relevance_score": str(doc.relevance_score)}
            for doc in search_results.results[:5]
        ]
        
        return VerificationResponse(
            status="success",
            summary=response_data["answer"],
            classification_score=classification_score,
            classification_label=classification_label,
            credibility_assessment=credibility_assessment,
            sources=sources,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in perform_verification: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

def determine_credibility(classification_score: float, source_count: int, ai_analysis: str) -> str:
    """Determine overall credibility assessment based on multiple factors."""
    try:
        # Factor in classification score
        if classification_score > 0.7:
            base_credibility = "HIGH_RISK"
        elif classification_score > 0.4:
            base_credibility = "MODERATE_RISK"
        else:
            base_credibility = "LOW_RISK"
        
        # Adjust based on source availability
        if source_count == 0:
            return "UNVERIFIABLE"
        elif source_count < 3:
            return "LIMITED_VERIFICATION"
        
        
        
        return base_credibility
        
    except Exception as e:
        logger.error(f"Error determining credibility: {e}")
        return "ANALYSIS_ERROR"

# Chat endpoint
@app.post("/chat")
async def chat_with_system(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Chat with the SCEPTRE system."""
    try:
        if request.session_id not in knowledge_bases:
            knowledge_bases[request.session_id] = KnowledgeBase(request.session_id)
        
        chat_history = []  # You might want to store this in a database
        response_data = await generate_response(
            request.query,
            chat_history,
            request.session_id,
            knowledge_bases
        )
        
        return {
            "answer": response_data["answer"],
            "sources": response_data["sources"],
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge base management
@app.post("/refresh-knowledge-base")
async def refresh_knowledge_base(
    request: RefreshKnowledgeBaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Refresh knowledge base with new topic information."""
    try:
        search_results = await search_documents(request.topic)
        
        if request.session_id not in knowledge_bases:
            knowledge_bases[request.session_id] = KnowledgeBase(request.session_id)
        
        kb = knowledge_bases[request.session_id]
        kb.add_documents(search_results.results)
        
        return {
            "message": f"Knowledge base refreshed with {len(search_results.results)} documents",
            "topic": request.topic,
            "document_count": len(search_results.results)
        }
        
    except Exception as e:
        logger.error(f"Error refreshing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "database": "connected",
            "classification_model": "loaded" if classification_model else "not loaded",
            "content_processor": "initialized" if content_processor else "not initialized"
        }
    }

# test the application
# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 10000))
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         reload=True,
#         log_level="info"
#     )