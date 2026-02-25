from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # issuer/user/merchant
    
    @field_validator("password")
    @classmethod
    def password_max_72_bytes(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password too long (max 72 bytes for bcrypt)")
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    id: int
    email: EmailStr
    role: str