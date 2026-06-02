from typing import Protocol

from app.services.change_detection.result import (
    ChangeDetectionEngineResult,
    ChecksumChangeDetectionRequest,
)


class ChangeDetectionEngine(Protocol):
    def detect(self, request: ChecksumChangeDetectionRequest) -> ChangeDetectionEngineResult:
        """Execute bounded acquisition-level change detection."""
