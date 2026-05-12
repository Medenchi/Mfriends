from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=48)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=10, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=48)
    username: str = Field(default="", max_length=32)
    bio: str = Field(default="", max_length=600)
    city: str = Field(default="", max_length=80)
    district: str = Field(default="", max_length=80)
    timezone: str = Field(default="UTC", max_length=64)
    buddy_goals: str = Field(default="", max_length=300)
    interests: str = Field(default="", max_length=300)
    games: str = Field(default="", max_length=300)
    hobbies: str = Field(default="", max_length=300)
    online_offline_preference: str = Field(default="both", pattern="^(online|offline|both)$")
    friendship_preference: str = Field(default="both", pattern="^(temporary|permanent|both)$")


class RequestCreate(BaseModel):
    receiver_id: int | None = None
    request_type: str = Field(default="friend", max_length=32)
    title: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=800)
    message: str = Field(default="", max_length=500)
    tags: str = Field(default="", max_length=240)
    category: str = Field(default="online", max_length=40)
    mode: str = Field(default="online", pattern="^(online|offline)$")
    reward: str = Field(default="", max_length=120)


class MessageCreate(BaseModel):
    chat_id: int
    body: str = Field(min_length=1, max_length=2000)
    attachment_url: str | None = Field(default=None, max_length=500)
    voice_placeholder: bool = False


class ReportCreate(BaseModel):
    reported_user_id: int | None = None
    message_id: int | None = None
    reason: str = Field(min_length=3, max_length=80)
    details: str = Field(default="", max_length=1000)


class VerificationStart(BaseModel):
    verification_type: str = Field(pattern="^(selfie|voice_code|liveness)$")


class BlockCreate(BaseModel):
    blocked_user_id: int
    reason: str = Field(default="", max_length=240)


class AdminDecision(BaseModel):
    status: str = Field(pattern="^(open|reviewing|resolved|dismissed)$")


class RefreshRequest(BaseModel):
    refresh_token: str
