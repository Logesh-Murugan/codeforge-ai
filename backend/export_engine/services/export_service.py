"""
ExportService — Phase 4.1

High-level façade that combines ReportService + ZipService.
Reads from the existing memory system to enrich the export bundle.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from export_engine.schemas import (
    AgentOutputData,
    ExportFormat,
    ExportRequest,
    ExportResult,
    GeneratedFile,
    ProjectBundle,
    ProjectMetadata,
    ReportType,
)
from export_engine.services.report_service import ReportService
from export_engine.services.zip_service import ZipService

logger = logging.getLogger(__name__)


class ExportService:
    """
    Orchestrates the full export pipeline:

    1. Build :class:`ProjectBundle` from agent runs + memory.
    2. Generate reports via :class:`ReportService`.
    3. Package everything via :class:`ZipService`.

    Args:
        memory_service: Optional injected MemoryService.  When ``None``,
                        the default auto-wired service is used.
    """

    def __init__(self, memory_service=None) -> None:
        if memory_service is None:
            try:
                from memory.manager import default_manager
                memory_service = default_manager.get_service()
            except Exception:
                memory_service = None
        self._memory = memory_service
        self._report_svc = ReportService()

    # ------------------------------------------------------------------
    # Build bundle from raw data
    # ------------------------------------------------------------------

    def build_bundle(
        self,
        project_id: int,
        project_title: str,
        project_description: Optional[str],
        project_status: str,
        agent_runs_raw: List[Dict[str, Any]],
        generated_files_raw: Optional[List[Dict[str, str]]] = None,
    ) -> ProjectBundle:
        """
        Construct a ProjectBundle from raw DB/orchestrator data.

        Args:
            project_id:          DB project ID.
            project_title:       Project title.
            project_description: Project description.
            project_status:      e.g. "completed".
            agent_runs_raw:      List of agent-run dicts from DB.
            generated_files_raw: List of {path, content} dicts.

        Returns:
            Populated :class:`ProjectBundle`.
        """
        metadata = ProjectMetadata(
            project_id=project_id,
            title=project_title,
            description=project_description,
            status=project_status,
        )

        # Parse agent outputs
        agent_outputs: List[AgentOutputData] = []
        for run in agent_runs_raw:
            agent_outputs.append(AgentOutputData(
                agent_name=run.get("agent_name", "unknown"),
                status=run.get("status", "unknown"),
                output_json=run.get("output_json"),
                error_message=run.get("error_message"),
                execution_time_seconds=run.get("execution_time_seconds"),
                retry_count=run.get("retry_count", 0),
                created_at=str(run.get("created_at", "")),
                updated_at=str(run.get("updated_at", "")),
            ))

        # Parse generated files
        gen_files: List[GeneratedFile] = []
        for f in (generated_files_raw or []):
            path = f.get("path", "")
            content = f.get("content", "")
            ext = path.rsplit(".", 1)[-1] if "." in path else "text"
            gen_files.append(GeneratedFile(path=path, content=content, language=ext))

        # Pull memory records if available
        memory_records: List[Dict[str, Any]] = []
        version_history: List[Dict[str, Any]] = []
        if self._memory:
            try:
                for col in ["requirements", "architecture", "backend_code", "frontend_code",
                            "security_reports", "qa_reports"]:
                    recs = self._memory.get_project_memory(project_id, col)
                    memory_records.extend(recs[:10])  # cap per-collection
                entries = self._memory.get_version_history(project_id)
                version_history = [
                    {
                        "version": e.version,
                        "agent_name": e.agent_name,
                        "artifact_type": e.artifact_type,
                        "timestamp": str(e.timestamp),
                    }
                    for e in entries
                ]
            except Exception as exc:
                logger.warning("[EXPORT] Memory read failed: %s", exc)

        return ProjectBundle(
            metadata=metadata,
            agent_outputs=agent_outputs,
            generated_files=gen_files,
            memory_records=memory_records,
            version_history=version_history,
        )

    # ------------------------------------------------------------------
    # Export as ZIP bytes
    # ------------------------------------------------------------------

    def export_zip(
        self,
        bundle: ProjectBundle,
        report_types: Optional[List[ReportType]] = None,
        include_source: bool = True,
    ) -> bytes:
        """
        Generate all reports and package everything into a ZIP.

        Returns:
            Raw ZIP bytes.
        """
        reports = self._report_svc.generate(bundle, report_types)
        zip_svc = ZipService(bundle.metadata.project_id)
        source = bundle.generated_files if include_source else []
        return zip_svc.build(reports, source)

    def export_source_zip(self, bundle: ProjectBundle) -> bytes:
        """Source code only ZIP."""
        zip_svc = ZipService(bundle.metadata.project_id)
        return zip_svc.build_source_only(bundle.generated_files)

    def export_reports_zip(
        self,
        bundle: ProjectBundle,
        report_types: Optional[List[ReportType]] = None,
    ) -> bytes:
        """Reports only ZIP."""
        reports = self._report_svc.generate(bundle, report_types)
        zip_svc = ZipService(bundle.metadata.project_id)
        return zip_svc.build_reports_only(reports)

    # ------------------------------------------------------------------
    # Generate ExportResult metadata
    # ------------------------------------------------------------------

    def describe_export(
        self,
        bundle: ProjectBundle,
        zip_bytes: bytes,
        report_types: Optional[List[ReportType]] = None,
    ) -> ExportResult:
        """Build an ExportResult summary for an export."""
        if report_types is None:
            report_types = [rt for rt in ReportType if rt != ReportType.FULL_PROJECT]
        return ExportResult(
            project_id=bundle.metadata.project_id,
            reports_generated=[rt.value for rt in report_types],
            total_files=len(bundle.generated_files) + len(report_types),
            zip_size_bytes=len(zip_bytes),
            success=True,
        )
