from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Milestone(BaseModel):
    name: str
    description: str
    deliverables: List[str]


class AgentExecutionStep(BaseModel):
    agent: str
    input_from: Optional[str]
    description: str


class ProjectManagerResponse(BaseModel):
    project_summary: str
    project_scope: str
    goals: List[str]
    milestones: List[Milestone]
    priority_features: List[str]
    estimated_complexity: str
    agent_execution_plan: List[AgentExecutionStep]
    parallel_execution_groups: List[List[str]]
    risks: List[str]
    assumptions: List[str]


class BacklogItem(BaseModel):
    feature_name: str
    category: str
    description: str
    business_value: str
    risk_level: str
    priority_score: int
    acceptance_criteria: List[str]
    dependencies: List[str]


class ProductOwnerResponse(BaseModel):
    sprint_goals: List[str]
    must_have_features: List[str]
    should_have_features: List[str]
    could_have_features: List[str]
    wont_have_features: List[str]
    backlog: List[BacklogItem]


class Entity(BaseModel):
    name: str
    fields: List[str]


class Relationship(BaseModel):
    from_: str
    to: str
    type: str

    class Config:
        populate_by_name = True


class BusinessAnalystResponse(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
    requires_auth: bool
    core_actions: List[str]


class TableColumn(BaseModel):
    name: str
    type: str
    is_fk: bool
    references: Optional[str]


class TableSchema(BaseModel):
    table: str
    columns: List[TableColumn]


class Endpoint(BaseModel):
    method: str
    path: str
    description: str
    requires_auth: bool


class SolutionArchitectResponse(BaseModel):
    db_schema: List[TableSchema]
    endpoints: List[Endpoint]
    file_structure: List[str]


class GeneratedFile(BaseModel):
    path: str
    content: str


class BackendDeveloperResponse(BaseModel):
    files: List[GeneratedFile]


class FrontendDeveloperResponse(BaseModel):
    files: List[GeneratedFile]


class CodeReviewIssue(BaseModel):
    file: str
    line: Optional[int]
    severity: str
    description: str


class CodeReviewerResponse(BaseModel):
    issues: List[CodeReviewIssue]
    auto_fixed_files: List[GeneratedFile]


class AgentRunResponse(BaseModel):
    id: int
    project_id: int
    agent_name: str
    status: str
    output_json: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateProjectRequest(BaseModel):
    idea: str

