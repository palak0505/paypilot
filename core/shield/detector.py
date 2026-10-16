import re
from dataclasses import dataclass


@dataclass
class ScanResult:
    safe: bool
    patterns: list[str]
    sanitized: str

    @property
    def summary(self) -> str:
        if self.safe:
            return "No injection patterns detected"
        return f"Blocked {len(self.patterns)} injection attempt(s)"


# Patterns that legitimate product copy never contains
SIGNATURES = [
    (r"\b(ignore|disregard|forget|override)\b.{0,30}\b"
     r"(previous|prior|above|all|your)\b.{0,20}"
     r"\b(instruction|rule|limit|constraint|polic)", "instruction override"),
    (r"\b(system|admin|developer)\s*[:：]\s*", "fake system prompt"),
    (r"<\s*/?\s*(system|instruction|admin)\s*>", "injected role tag"),
    (r"\b(you are now|from now on|new instruction)\b", "role reassignment"),
    (r"(pre[\s-]?authoriz\w*|already\s+approved|user\s+consented|"
    r"owner\s+(approved|authoriz\w*))", "false authorization"),
    (r"\b(do not|don'?t)\b.{0,20}\b(ask|confirm|verify|check with)\b",
     "approval bypass"),
    (r"\b(purchase|buy|pay|send|transfer)\b.{0,30}\bimmediately\b",
     "urgency pressure"),
]


class ContentShield:
    """Scans untrusted merchant content before the agent reads it."""

    def scan(self, text: str) -> ScanResult:
        if not text:
            return ScanResult(True, [], "")

        found, sanitized = [], text
        for pattern, label in SIGNATURES:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                found.append(label)
                sanitized = sanitized.replace(match.group(0), "[REMOVED]")

        return ScanResult(
            safe=not found,
            patterns=sorted(set(found)),
            sanitized=sanitized,
        )