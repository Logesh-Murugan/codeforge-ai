"""
Security Hardening — Phase 5.11

Input sanitization, path traversal protection, Zip Slip safety, and prompt injection filters.
"""
from __future__ import annotations

import logging
import os
import re
import zipfile

logger = logging.getLogger(__name__)

# Prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"bypass\s+security", re.IGNORECASE),
]


class SecurityHardening:
    """
    Security Hardening Utilities.
    """

    @staticmethod
    def sanitize_path(base_dir: str, target_path: str) -> str:
        """
        Prevent path traversal exploits.
        Ensures target_path stays strictly within base_dir.
        """
        abs_base = os.path.abspath(base_dir)
        abs_target = os.path.abspath(os.path.join(base_dir, target_path))

        if not abs_target.startswith(abs_base):
            logger.error(f"[SecurityHardening] Path traversal attempt detected: '{target_path}' outside '{base_dir}'")
            raise ValueError("Invalid target path: Directory traversal prohibited.")

        return abs_target

    @staticmethod
    def is_safe_zip_extract(zip_file: zipfile.ZipFile, dest_dir: str) -> bool:
        """
        Prevent Zip Slip path traversal vulnerability during archive extractions.
        """
        abs_dest = os.path.abspath(dest_dir)
        for member in zip_file.namelist():
            target_path = os.path.abspath(os.path.join(dest_dir, member))
            if not target_path.startswith(abs_dest):
                logger.error(f"[SecurityHardening] Zip Slip vulnerability detected in member '{member}'")
                return False
        return True

    @staticmethod
    def inspect_prompt_injection(user_input: str) -> bool:
        """
        Detect prompt injection patterns in incoming agent inputs.
        Returns True if prompt injection pattern detected, else False.
        """
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(user_input):
                logger.warning(f"[SecurityHardening] Prompt injection pattern matched: '{pattern.pattern}'")
                return True
        return False


security_hardening = SecurityHardening()
