"""
CyberTrap - Pydantic Validators with Soft-Fail Logic
Validates extracted intelligence data with auto-cleaning
"""

import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class ScamIntelligence(BaseModel):
    """Validated scam intelligence data with soft-fail cleaning"""
    
    upi: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc: Optional[str] = None
    link: Optional[str] = None
    raw_upi: Optional[str] = None  # Original before cleaning
    raw_bank: Optional[str] = None
    raw_ifsc: Optional[str] = None
    needs_clarification: Optional[str] = None  # Field needing clarification
    
    @field_validator('upi', mode='before')
    @classmethod
    def clean_upi(cls, v):
        """Clean and validate UPI ID with soft-fail"""
        if not v:
            return None
        
        original = v
        # Soft-fail cleaning: remove spaces, dashes, common typos
        v = v.strip().lower()
        v = v.replace(" ", "").replace("-", "").replace("_", "")
        v = v.replace("@ok", "@ok")  # normalize
        
        # UPI regex pattern
        upi_pattern = r'^[a-zA-Z0-9.]{2,256}@[a-zA-Z]{2,64}$'
        
        if re.match(upi_pattern, v):
            return v
        
        # If still has @ but doesn't match, might be close - return for clarification
        if '@' in v:
            return v  # Return anyway, will trigger clarification
        
        return None
    
    @field_validator('bank_account', mode='before')
    @classmethod
    def clean_bank_account(cls, v):
        """Clean and validate bank account number"""
        if not v:
            return None
        
        # Remove all non-digits
        v = re.sub(r'\D', '', str(v))
        
        # Indian bank accounts are 9-18 digits
        if 9 <= len(v) <= 18:
            return v
        
        # If close to valid length, return for clarification
        if 6 <= len(v) <= 20:
            return v
        
        return None
    
    @field_validator('ifsc', mode='before')
    @classmethod
    def clean_ifsc(cls, v):
        """Clean and validate IFSC code"""
        if not v:
            return None
        
        # Clean and uppercase
        v = v.strip().upper().replace(" ", "").replace("-", "")
        
        # IFSC pattern: 4 letters + 0 + 6 alphanumeric
        ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        
        if re.match(ifsc_pattern, v):
            return v
        
        # If 11 chars and starts with letters, might be close
        if len(v) == 11 and v[:4].isalpha():
            return v
        
        return None
    
    @field_validator('link', mode='before')
    @classmethod
    def clean_link(cls, v):
        """Extract and validate URLs"""
        if not v:
            return None
        
        # URL pattern
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, str(v))
        
        if match:
            return match.group(0)
        
        # Check for partial URLs
        if any(x in str(v).lower() for x in ['.com', '.in', '.net', '.org', 'bit.ly', 't.co']):
            return v.strip()
        
        return None


class ExtractionHistory(BaseModel):
    """Tracks extraction history for consensus confidence"""
    
    upi_extractions: list[tuple[int, str]] = []  # (turn_number, value)
    bank_extractions: list[tuple[int, str]] = []
    ifsc_extractions: list[tuple[int, str]] = []
    link_extractions: list[tuple[int, str]] = []
    
    # Consensus flags - True when same value extracted 2+ times
    upi_consensus: bool = False
    bank_consensus: bool = False
    ifsc_consensus: bool = False
    link_consensus: bool = False


class ConversationState(BaseModel):
    """Tracks conversation state for staged extraction"""
    
    current_stage: int = 1
    stage_turns: int = 0
    total_turns: int = 0
    intelligence_collected: ScamIntelligence = ScamIntelligence()
    detected_language: str = "english"
    extraction_allowed: bool = False
    extraction_history: ExtractionHistory = ExtractionHistory()
    
    @model_validator(mode='after')
    def check_extraction_allowed(self):
        """Enable extraction only after minimum rapport turns"""
        from persona import MIN_RAPPORT_TURNS
        self.extraction_allowed = self.total_turns >= MIN_RAPPORT_TURNS
        return self


class EngageRequest(BaseModel):
    """Request model for /api/engage endpoint"""
    
    message: str
    conversation_history: list = []
    session_id: Optional[str] = None


class ThoughtStep(BaseModel):
    """Single step in agent's thought process"""
    
    type: str  # "thought", "action", "tool_call", "validation"
    content: str


class IntelligenceData(BaseModel):
    """Structured intelligence data for API response"""
    
    upi: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc: Optional[str] = None
    link: Optional[str] = None


class EngageResponse(BaseModel):
    """
    Response model for /api/engage endpoint
    Matches hackathon evaluation schema exactly
    """
    
    # Required fields per hackathon spec
    classification: str = "SCAM"  # Always SCAM for honey-pot
    confidence: float  # 0.0 to 1.0 score
    reply: str  # Mrs. Shanthi's response
    intelligence: IntelligenceData  # Extracted data
    explanation: str  # Agent's reasoning
    
    # Extended fields for UI/debugging
    current_stage: int
    detected_language: str
    thought_process: list[ThoughtStep]
    needs_clarification: Optional[str] = None
    extraction_allowed: bool = True


def validate_and_flag(data: dict) -> tuple[ScamIntelligence, Optional[str]]:
    """
    Validate intelligence data and return field needing clarification.
    Returns (validated_data, field_needing_clarification)
    """
    intel = ScamIntelligence(**data)
    clarification_needed = None
    
    # Check if any field needs clarification (has data but might be invalid)
    if intel.upi and not re.match(r'^[a-zA-Z0-9.]{2,256}@[a-zA-Z]{2,64}$', intel.upi):
        clarification_needed = "upi"
    elif intel.bank_account and not (9 <= len(intel.bank_account) <= 18):
        clarification_needed = "bank_account"
    elif intel.ifsc and not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', intel.ifsc):
        clarification_needed = "ifsc"
    
    intel.needs_clarification = clarification_needed
    return intel, clarification_needed
