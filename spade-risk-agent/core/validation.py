from pydantic import BaseModel, Field, field_validator
from typing import Optional


class AssessmentInput(BaseModel):
    """Input model for risk assessment reqests"""
    address: str = Field(..., min_length=1, description="Property address")
    property_type: str = Field(..., description="Type of property")
    fenced: bool
    gated: bool
    operating_hours: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('property_type')
    @classmethod
    def validate_property_type(cls, v):
        """Make sure property type is valid - normalize to lowercase"""
        allowed_types = {"home", "rental", "vacation home", "business"}
        v_lower = v.lower() if isinstance(v, str) else str(v).lower()
        if v_lower not in allowed_types:
            raise ValueError(f"property_type must be one of: {', '.join(sorted(allowed_types))}")
        return v_lower
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Trim whitespace and make sure it's not empty"""
        if not v or not v.strip():
            raise ValueError("address cannot be empty")
        return v.strip()



