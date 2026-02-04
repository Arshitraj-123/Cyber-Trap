"""
CyberTrap - Agentic Scam Intelligence Honey-Pot
FastAPI Backend with Groq LLM (Llama 3.3 70B)

Features:
- X-API-Key authentication
- Language detection layer
- 4-stage extraction funnel with buffer logic
- Stealth intelligence gathering
- Retry logic for rate limiting
"""

import os
import re
import json
import random
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from groq import Groq
from groq import RateLimitError

from persona import (
    SYSTEM_PROMPT, STAGE_HOOK, STAGE_FRICTION, STAGE_PIVOT, STAGE_EXTRACTION,
    STAGE_DESCRIPTIONS, MIN_RAPPORT_TURNS, CLARIFICATION_PROMPTS, LANGUAGE_HINTS
)
from validators import (
    ScamIntelligence, ConversationState, EngageRequest, EngageResponse, SimpleEngageResponse,
    ThoughtStep, validate_and_flag, IntelligenceData
)

# Load environment variables
load_dotenv()

# Configure Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "cybertrap-secret-key-2024")

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

# In-memory session storage (use Redis in production)
sessions: dict[str, ConversationState] = {}


def detect_language(text: str) -> str:
    """Detect language using keyword heuristics"""
    text_lower = text.lower()
    
    # Count language hint matches
    scores = {}
    for lang, hints in LANGUAGE_HINTS.items():
        score = sum(1 for hint in hints if hint in text_lower)
        if score > 0:
            scores[lang] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    # Try langdetect as fallback
    try:
        from langdetect import detect
        detected = detect(text)
        lang_map = {"hi": "hindi", "ta": "tamil", "te": "telugu", "ml": "malayalam", "en": "english"}
        return lang_map.get(detected, "english")
    except:
        return "english"


def extract_intelligence_from_text(text: str) -> dict:
    """Regex-based extraction as backup"""
    intel = {}
    
    # UPI pattern
    upi_match = re.search(r'[a-zA-Z0-9._-]+@[a-zA-Z]{2,}', text)
    if upi_match:
        intel["upi"] = upi_match.group(0)
    
    # Bank account (9-18 digits)
    bank_match = re.search(r'\b\d{9,18}\b', text)
    if bank_match:
        intel["bank_account"] = bank_match.group(0)
    
    # IFSC code
    ifsc_match = re.search(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', text, re.IGNORECASE)
    if ifsc_match:
        intel["ifsc"] = ifsc_match.group(0).upper()
    
    # URLs
    url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    if url_match:
        intel["link"] = url_match.group(0)
    
    return intel


def get_clarification_prompt(field: str, value: str) -> str:
    """Get a natural clarification prompt for invalid data"""
    prompts = CLARIFICATION_PROMPTS.get(field, [])
    if prompts:
        return random.choice(prompts).format(value=value)
    return f"Sorry beta, can you repeat that {field} again?"


def calculate_consensus_confidence(
    new_intel: dict,
    state: ConversationState,
    base_confidence: float
) -> tuple[float, list[ThoughtStep]]:
    """
    Calculate cumulative confidence with consensus boost.
    Returns (final_confidence, thought_steps)
    
    Confidence Levels:
    - 0.50: Base extraction
    - 0.65: Regex match confirmed
    - 0.75: Turn count > 4
    - 1.00: Consensus achieved (same value extracted 2+ times)
    """
    thought_steps = []
    confidence = base_confidence
    history = state.extraction_history
    turn = state.total_turns
    
    # Track new extractions and check for consensus
    consensus_achieved = False
    
    # UPI consensus check
    if new_intel.get("upi"):
        new_val = new_intel["upi"]
        # Check if this value was extracted before
        previous_vals = [v for (t, v) in history.upi_extractions if v == new_val]
        if previous_vals:
            history.upi_consensus = True
            consensus_achieved = True
            thought_steps.append(ThoughtStep(
                type="validation",
                content=f"🔒 CONSENSUS: UPI '{new_val}' confirmed across multiple turns. Locking record."
            ))
        # Add to history
        history.upi_extractions.append((turn, new_val))
    
    # Bank account consensus check
    if new_intel.get("bank_account"):
        new_val = new_intel["bank_account"]
        previous_vals = [v for (t, v) in history.bank_extractions if v == new_val]
        if previous_vals:
            history.bank_consensus = True
            consensus_achieved = True
            thought_steps.append(ThoughtStep(
                type="validation",
                content=f"🔒 CONSENSUS: Bank Account '{new_val}' confirmed across multiple turns. Locking record."
            ))
        history.bank_extractions.append((turn, new_val))
    
    # IFSC consensus check
    if new_intel.get("ifsc"):
        new_val = new_intel["ifsc"]
        previous_vals = [v for (t, v) in history.ifsc_extractions if v == new_val]
        if previous_vals:
            history.ifsc_consensus = True
            consensus_achieved = True
            thought_steps.append(ThoughtStep(
                type="validation",
                content=f"🔒 CONSENSUS: IFSC '{new_val}' confirmed across multiple turns. Locking record."
            ))
        history.ifsc_extractions.append((turn, new_val))
    
    # Link consensus check
    if new_intel.get("link"):
        new_val = new_intel["link"]
        previous_vals = [v for (t, v) in history.link_extractions if v == new_val]
        if previous_vals:
            history.link_consensus = True
            consensus_achieved = True
            thought_steps.append(ThoughtStep(
                type="validation",
                content=f"🔒 CONSENSUS: Link confirmed across multiple turns. Locking record."
            ))
        history.link_extractions.append((turn, new_val))
    
    # Calculate final confidence
    if consensus_achieved:
        # CONSENSUS BOOST: 100% confidence when same value extracted twice
        confidence = 1.00
        thought_steps.append(ThoughtStep(
            type="action",
            content="📊 Confidence: 100% (Consensus achieved - data immutable)"
        ))
    else:
        # Cumulative confidence calculation
        if new_intel:  # Has extraction
            confidence = 0.50  # Base for first extraction
            
            # Regex match bonus
            confidence += 0.15  # Now 65%
            
            # Turn count bonus
            if turn > 4:
                confidence += 0.10  # Now 75%
            
            thought_steps.append(ThoughtStep(
                type="action",
                content=f"📊 Confidence: {int(confidence * 100)}% (awaiting consensus for 100%)"
            ))
    
    return confidence, thought_steps


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
async def call_groq_with_retry(messages: list) -> str:
    """Call Groq with retry logic for rate limiting"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.8,
        max_tokens=300,
        top_p=0.9
    )
    return response.choices[0].message.content


async def process_with_groq(
    message: str,
    state: ConversationState,
    history: list
) -> tuple[str, dict, list[ThoughtStep], float]:
    """Process message through Groq LLM"""
    
    thought_process = []
    extracted_intel = {}
    confidence = 0.0
    
    # Build conversation context
    history_text = "\n".join([
        f"{'Scammer' if msg.get('role') == 'scammer' else 'Mrs. Shanthi'}: {msg.get('content', '')}"
        for msg in history[-10:]  # Last 10 messages for context
    ])
    
    # Format system prompt with current state
    formatted_prompt = SYSTEM_PROMPT.format(
        current_stage=state.current_stage,
        stage_turns=state.stage_turns
    )
    
    # Add stage buffer logic
    stage_instruction = ""
    if not state.extraction_allowed:
        stage_instruction = f"\n\n⚠️ STAGE BUFFER ACTIVE: You have only had {state.total_turns} turns. Build more rapport before attempting extraction. Stay in Stage 1-2."
    
    thought_process.append(ThoughtStep(
        type="thought",
        content=f"Stage {state.current_stage}: {STAGE_DESCRIPTIONS.get(state.current_stage, 'Unknown')}"
    ))
    
    # Check if Groq is configured
    if not groq_client:
        # Fallback mode without LLM
        thought_process.append(ThoughtStep(
            type="thought",
            content="Running in demo mode (no API key). Using template response."
        ))
        
        # Extract any intelligence from the message
        extracted_intel = extract_intelligence_from_text(message)
        
        # Generate template response based on stage
        if state.current_stage == STAGE_HOOK:
            reply = "Aiyyo! This is very interesting, beta! I am very excited to hear more! Please tell me all the details about this opportunity?"
        elif state.current_stage == STAGE_FRICTION:
            reply = "Beta, I want to do this but my grandson installed some NetProtect software and it is showing warnings. I am not good with technology. Is there some other way I can proceed?"
        elif state.current_stage == STAGE_PIVOT:
            reply = "I am trying to pay, but my grandson is not here to help me. Can you give me your UPI ID or Bank account? My neighbor Lakshmi's son said he can do the transfer for me if I give him the details."
        else:
            reply = "Let me write this down slowly, beta... Can you repeat that again? My eyes are not so good nowadays."
        
        confidence = 0.5 if extracted_intel else 0.2
        return reply, extracted_intel, thought_process, confidence
    
    try:
        # Build messages for Groq
        messages = [
            {
                "role": "system",
                "content": f"{formatted_prompt}{stage_instruction}"
            }
        ]
        
        # Add conversation history
        for msg in history[-6:]:  # Last 6 messages for context
            role = "user" if msg.get("role") == "scammer" else "assistant"
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        print(f"[CyberTrap] Calling Groq with message: {message[:50]}...")
        
        # Call Groq
        reply = await call_groq_with_retry(messages)
        
        print(f"[CyberTrap] Groq response received: {reply[:100]}...")
        
        if not reply:
            print("[CyberTrap] Empty Groq response, using contextual fallback")
            reply = "Aiyyo beta, I didn't understand. Can you explain again slowly?"
        
        thought_process.append(ThoughtStep(
            type="action",
            content=f"Groq LLM response generated ({len(reply)} chars)"
        ))
        
        # Do regex extraction from the scammer's message
        regex_intel = extract_intelligence_from_text(message)
        for key, value in regex_intel.items():
            if key not in extracted_intel:
                extracted_intel[key] = value
                thought_process.append(ThoughtStep(
                    type="tool_call",
                    content=f"🔒 Stealth extracted {key}: {value[:25]}..."
                ))
        
        # Set confidence based on extraction
        if extracted_intel:
            confidence = 0.75
        else:
            confidence = 0.4
        
        return reply, extracted_intel, thought_process, confidence
        
    except Exception as e:
        print(f"[CyberTrap] ❌ EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        thought_process.append(ThoughtStep(
            type="thought",
            content=f"API Error: {str(e)[:100]}. Using fallback."
        ))
        
        # Fallback response based on stage
        if state.current_stage == STAGE_HOOK:
            reply = "Aiyyo! This sounds very interesting, beta! Please tell me more about this opportunity?"
        elif state.current_stage == STAGE_FRICTION:
            reply = "Beta, I want to proceed but my NetProtect software is showing some warning. Is there any other way I can do this?"
        elif state.current_stage == STAGE_PIVOT:
            reply = "I am trying to pay, but my grandson is not here. Can you give me your UPI ID or Bank account? My neighbor's son said he can do the transfer."
        else:
            reply = "Konjam wait pannunga beta, let me write this down slowly..."
        
        extracted_intel = extract_intelligence_from_text(message)
        
        return reply, extracted_intel, thought_process, 0.3


# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🕷️ CyberTrap Backend Starting...")
    print(f"   Groq API: {'✓ Configured' if GROQ_API_KEY else '✗ Not configured (demo mode)'}")
    yield
    print("🕷️ CyberTrap Backend Shutting down...")


app = FastAPI(
    title="CyberTrap API",
    description="Agentic Scam Intelligence Honey-Pot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from header"""
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "CyberTrap Honey-Pot",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "groq_configured": bool(GROQ_API_KEY),
        "active_sessions": len(sessions)
    }


@app.post("/api/engage", response_model=SimpleEngageResponse)
async def engage_scammer(
    request: EngageRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main engagement endpoint.
    Processes scammer message through Mrs. Shanthi persona.
    
    Headers:
        X-API-Key: API authentication key
    
    Request Body:
        message: The scammer's message (string or object)
        conversation_history: Previous conversation turns
        session_id: Optional session identifier
    
    Returns:
        status: "success"
        reply: Mrs. Shanthi's response
    """
    
    thought_process = []
    
    # Extract message text if it's a dictionary/object
    message_text = request.message
    if isinstance(request.message, dict):
        message_text = request.message.get("text", "")
    elif not isinstance(request.message, str):
        message_text = str(request.message)
    
    # Get or create session state
    session_id = request.session_id or "default"
    if session_id not in sessions:
        sessions[session_id] = ConversationState()
    
    state = sessions[session_id]
    
    # Language detection
    detected_lang = detect_language(message_text)
    state.detected_language = detected_lang
    
    thought_process.append(ThoughtStep(
        type="thought",
        content=f"Language detected: {detected_lang}"
    ))
    
    # Update turn counters
    state.total_turns += 1
    state.stage_turns += 1
    
    # Check stage buffer
    if state.total_turns < MIN_RAPPORT_TURNS:
        thought_process.append(ThoughtStep(
            type="thought",
            content=f"Stage buffer active: {state.total_turns}/{MIN_RAPPORT_TURNS} turns"
        ))
        state.extraction_allowed = False
    else:
        state.extraction_allowed = True
    
    # Process with Groq
    reply, new_intel, groq_thoughts, confidence = await process_with_groq(
        message_text,
        state,
        request.conversation_history
    )
    
    thought_process.extend(groq_thoughts)
    
    # Validate and merge intelligence
    validated_intel, needs_clarification = validate_and_flag(new_intel)
    
    # Calculate consensus-based confidence
    final_confidence, consensus_thoughts = calculate_consensus_confidence(
        new_intel, state, confidence
    )
    thought_process.extend(consensus_thoughts)
    
    # Merge with existing intelligence
    current_intel = state.intelligence_collected
    if validated_intel.upi and not current_intel.upi:
        current_intel.upi = validated_intel.upi
    if validated_intel.bank_account and not current_intel.bank_account:
        current_intel.bank_account = validated_intel.bank_account
    if validated_intel.ifsc and not current_intel.ifsc:
        current_intel.ifsc = validated_intel.ifsc
    if validated_intel.link and not current_intel.link:
        current_intel.link = validated_intel.link
    
    state.intelligence_collected = current_intel
    
    # Handle clarification if needed
    if needs_clarification:
        clarification_prompt = get_clarification_prompt(
            needs_clarification,
            getattr(validated_intel, needs_clarification, "")
        )
        thought_process.append(ThoughtStep(
            type="validation",
            content=f"Data needs clarification: {needs_clarification}"
        ))
        # Append clarification to reply
        reply = f"{reply} {clarification_prompt}"
    
    # Auto-advance stages based on collected intelligence
    if state.extraction_allowed:
        if current_intel.upi or current_intel.bank_account:
            if state.current_stage < STAGE_EXTRACTION:
                state.current_stage = STAGE_EXTRACTION
                state.stage_turns = 0
                thought_process.append(ThoughtStep(
                    type="action",
                    content="Auto-advanced to Stage 4 (Extraction complete)"
                ))
        elif state.current_stage == STAGE_HOOK and state.stage_turns >= 2:
            state.current_stage = STAGE_FRICTION
            state.stage_turns = 0
    
    # Return simplified response for hackathon
    return SimpleEngageResponse(
        status="success",
        reply=reply
    )


@app.post("/api/reset")
async def reset_session(
    session_id: str = "default",
    api_key: str = Depends(verify_api_key)
):
    """Reset a conversation session"""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "reset", "session_id": session_id}


@app.get("/api/sessions")
async def list_sessions(api_key: str = Depends(verify_api_key)):
    """List active sessions (debug endpoint)"""
    return {
        "count": len(sessions),
        "sessions": [
            {
                "id": sid,
                "stage": state.current_stage,
                "turns": state.total_turns,
                "has_intel": bool(state.intelligence_collected.upi or state.intelligence_collected.bank_account)
            }
            for sid, state in sessions.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
