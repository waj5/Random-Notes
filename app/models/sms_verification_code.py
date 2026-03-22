from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SmsVerificationCode(SQLModel, table=True):
    __tablename__ = "sms_verification_codes"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(index=True, max_length=20)
    purpose: str = Field(index=True, max_length=20)
    code_hash: str = Field(max_length=255)
    expires_at: datetime = Field(nullable=False, index=True)
    used_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
