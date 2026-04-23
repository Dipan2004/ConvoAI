import re
from typing import Optional, Tuple

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_NAME_RE = re.compile(r"^[a-zA-Z\s'\-]{2,60}$")


class LeadValidator:
    def validate_field(self, field: str, value: str) -> Tuple[bool, Optional[str]]:
        dispatch = {
            "name": self.validate_name,
            "email": self.validate_email,
            "platform": self.validate_platform,
        }
        fn = dispatch.get(field)
        if fn is None:
            return False, f"Unknown field: {field}"
        return fn(value)

    def validate_name(self, value: str) -> Tuple[bool, Optional[str]]:
        v = value.strip()
        if not v:
            return False, "Name cannot be empty."
        if not _NAME_RE.match(v):
            return False, "Name must contain only letters and spaces (2-60 chars)."
        return True, None

    def validate_email(self, value: str) -> Tuple[bool, Optional[str]]:
        v = value.strip().lower()
        if not v:
            return False, "Email cannot be empty."
        if not _EMAIL_RE.match(v):
            return False, "Please provide a valid email address."
        return True, None

    def validate_platform(self, value: str) -> Tuple[bool, Optional[str]]:
        v = value.strip()
        if not v or len(v) < 2:
            return False, "Please specify the platform or product."
        if len(v) > 100:
            return False, "Platform name is too long."
        return True, None