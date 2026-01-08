from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Auth:
    """Simple auth container.

    Prefer API key in headers:
      Authorization: Bearer <token>
    """

    api_key: Optional[str] = None
    header_name: str = "Authorization"
    bearer_prefix: str = "Bearer"

    def headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        if self.header_name.lower() == "authorization":
            return {self.header_name: f"{self.bearer_prefix} {self.api_key}".strip()}
        return {self.header_name: self.api_key}
