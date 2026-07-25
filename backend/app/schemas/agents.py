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


class DBIndex(BaseModel):
    name: str
    table: str
    columns: List[str]
    unique: bool


class DBRelationship(BaseModel):
    name: str
    from_table: str
    from_columns: List[str]
    to_table: str
    to_columns: List[str]
    cardinality: str  # one_to_many, one_to_one, many_to_many


class DatabaseEngineerResponse(BaseModel):
    er_diagram_mermaid: str
    db_schema_details: str
    indexes: List[DBIndex]
    relationships: List[DBRelationship]
    migration_plan: List[str]
    normalization_review: str
    sqlalchemy_models_code: str



class SecurityFinding(BaseModel):
    category: str          # e.g. "JWT", "OWASP:A01", "Injection", "Auth", "Secrets", "Dependencies"
    owasp_id: Optional[str]  # e.g. "A01:2021", "A03:2021" — null if not directly mapped
    severity: str          # "critical" | "high" | "medium" | "low" | "info"
    file: Optional[str]    # affected file path if applicable
    line: Optional[int]    # affected line number if known
    title: str
    description: str
    recommendation: str
    code_snippet: Optional[str]  # offending code snippet if applicable


class SecurityEngineerResponse(BaseModel):
    overall_risk: str                    # "critical" | "high" | "medium" | "low"
    findings: List[SecurityFinding]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    jwt_assessment: str
    dependency_risks: List[str]
    secrets_detected: List[str]
    owasp_coverage: List[str]            # OWASP IDs checked
    recommended_patches: List[str]       # ordered list of patch instructions


class TestCase(BaseModel):
    name: str
    type: str                  # "unit" | "integration" | "api" | "edge_case"
    description: str
    input_mock: str
    expected_output: str


class QAEngineerResponse(BaseModel):
    test_plan: str
    unit_tests_code: str
    integration_tests_code: str
    api_tests_code: str
    edge_cases: List[TestCase]
    coverage_report_summary: str
    estimated_coverage: float


class EnvVarConfig(BaseModel):
    name: str
    description: str
    default_value: Optional[str] = None
    is_secret: bool


class DevOpsEngineerResponse(BaseModel):
    dockerfile: str
    docker_compose: str
    github_actions_workflow: str
    nginx_config: str
    production_env_vars: List[EnvVarConfig]
    deployment_guide: str


class APIEndpoint(BaseModel):
    path: str
    method: str
    summary: str
    request_model: Optional[str]
    response_model: Optional[str] = None
    error_responses: List[str]
    auth_required: bool


class APIRequestModel(BaseModel):
    name: str
    fields: List[dict]


class APIResponseModel(BaseModel):
    name: str
    fields: List[dict]


class APIErrorModel(BaseModel):
    status_code: int
    error_code: str
    description: str
    example_response: str


class AuthenticationFlow(BaseModel):
    method: str
    token_endpoint: str
    refresh_endpoint: str
    description: str


class APIDesignerResponse(BaseModel):
    openapi_spec: str
    endpoints: List[APIEndpoint]
    request_models: List[APIRequestModel]
    response_models: List[APIResponseModel]
    error_models: List[APIErrorModel]
    authentication_flow: AuthenticationFlow
    versioning_strategy: str


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

