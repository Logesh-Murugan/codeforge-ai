"""
Human Approval Workflow System — Phase 5.3

Provides interactive human-in-the-loop control for the CodeForge AI agent pipeline.

Supported Operations:
    - Approve: Accept current agent output and continue to next node.
    - Reject: Reject output and safely halt pipeline execution.
    - Regenerate: Re-run the current node to generate fresh output.
    - Edit: Override/modify output JSON before approval/continuing.
    - Continue: Resume execution from a paused checkpoint.
"""
__version__ = "5.3.0"
