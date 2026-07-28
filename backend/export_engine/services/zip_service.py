"""
ZipService — Phase 4.1

Packages all generated reports + source code into a single ZIP archive.
Returns raw bytes suitable for streaming as a FastAPI response.
"""
from __future__ import annotations

import io
import logging
import zipfile
from typing import List, Optional

from export_engine.schemas import GeneratedFile, GeneratedReport

logger = logging.getLogger(__name__)


class ZipService:
    """
    Assembles a ProjectBundle ZIP from reports and source code files.

    ZIP layout::

        GeneratedProject_<id>/
        ├── source_code/
        │   ├── backend/...
        │   └── frontend/...
        ├── README.md
        ├── Architecture_Report.md
        ├── API_Documentation.md
        ├── Database_Schema.md
        ├── ER_Diagram.md
        ├── Security_Report.md
        ├── Testing_Report.md
        ├── Deployment_Guide.md
        ├── Memory_Report.md
        ├── Agent_Execution_Report.md
        ├── Version_Report.md
        └── RAG_Context_Report.md
    """

    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        self._root = f"GeneratedProject_{project_id}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        reports: List[GeneratedReport],
        source_files: Optional[List[GeneratedFile]] = None,
    ) -> bytes:
        """
        Build and return the ZIP archive as bytes.

        Args:
            reports:      All generated reports (Markdown).
            source_files: Generated source code files.

        Returns:
            Raw ZIP bytes.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            self._add_reports(zf, reports)
            if source_files:
                self._add_source_files(zf, source_files)
        buf.seek(0)
        data = buf.read()
        logger.info(
            "[ZIP] Built ZIP for project %d: %d reports, %d source files, %d bytes",
            self.project_id, len(reports), len(source_files or []), len(data),
        )
        return data

    def build_source_only(self, source_files: List[GeneratedFile]) -> bytes:
        """Build a source-code-only ZIP (no reports)."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            self._add_source_files(zf, source_files)
        buf.seek(0)
        return buf.read()

    def build_reports_only(self, reports: List[GeneratedReport]) -> bytes:
        """Build a reports-only ZIP."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            self._add_reports(zf, reports)
        buf.seek(0)
        return buf.read()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _add_reports(
        self,
        zf: zipfile.ZipFile,
        reports: List[GeneratedReport],
    ) -> None:
        for report in reports:
            arcname = f"{self._root}/{report.filename}"
            zf.writestr(arcname, report.content)
            logger.debug("[ZIP] Added report: %s", arcname)

    def _add_source_files(
        self,
        zf: zipfile.ZipFile,
        source_files: List[GeneratedFile],
    ) -> None:
        for sf in source_files:
            # Normalise Windows-style paths
            clean_path = sf.path.replace("\\", "/").lstrip("/")
            arcname = f"{self._root}/source_code/{clean_path}"
            zf.writestr(arcname, sf.content)
            logger.debug("[ZIP] Added source: %s", arcname)
