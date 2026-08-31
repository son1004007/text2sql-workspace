from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import AuthenticatedIdentity, issue_demo_token, verify_demo_token
from app.evaluation import EvaluationRunner
from app.schemas import (
    AccessTokenResponse,
    DemoTokenRequest,
    EvaluationCaseResponse,
    EvaluationSummaryResponse,
    QueryCreate,
    QueryResponse,
    WorkspaceCreate,
    WorkspaceResponse,
)
from app.service import ResourceNotFound, Text2SqlWorkspaceService


router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer(auto_error=False)


def get_service(request: Request) -> Text2SqlWorkspaceService:
    return request.app.state.service


def get_evaluation_runner(request: Request) -> EvaluationRunner:
    return request.app.state.evaluation_runner


def current_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_demo_token(
        credentials.credentials,
        secret=request.app.state.settings.auth_secret,
    )


def not_found_guard(call):
    try:
        return call()
    except ResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/auth/demo-token", response_model=AccessTokenResponse, tags=["auth"])
def create_demo_token(request: Request, body: DemoTokenRequest) -> AccessTokenResponse:
    try:
        token = issue_demo_token(
            body.username,
            secret=request.app.state.settings.auth_secret,
            ttl_seconds=request.app.state.settings.access_token_ttl_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="DEMO_USER_NOT_FOUND") from exc
    return AccessTokenResponse(access_token=token)


@router.post(
    "/evaluations/run",
    response_model=EvaluationSummaryResponse,
    tags=["evaluation"],
)
def run_evaluation(
    _: AuthenticatedIdentity = Depends(current_identity),
    runner: EvaluationRunner = Depends(get_evaluation_runner),
) -> EvaluationSummaryResponse:
    summary = runner.run()
    return EvaluationSummaryResponse(
        total=summary.total,
        generation_success=summary.generation_success,
        validation_success=summary.validation_success,
        execution_success=summary.execution_success,
        correctness_success=summary.correctness_success,
        cases=[
            EvaluationCaseResponse(
                case_id=case.case_id,
                question=case.question,
                generation_success=case.generation_success,
                validation_success=case.validation_success,
                execution_success=case.execution_success,
                correctness_success=case.correctness_success,
                failure_code=case.failure_code,
                candidate_sql=case.candidate_sql,
            )
            for case in summary.cases
        ],
    )


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["workspaces"],
)
def create_workspace(
    body: WorkspaceCreate,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> WorkspaceResponse:
    return not_found_guard(
        lambda: service.create_workspace(user_id=identity.user_id, name=body.name)
    )


@router.get("/workspaces", response_model=list[WorkspaceResponse], tags=["workspaces"])
def list_workspaces(
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> list[WorkspaceResponse]:
    return not_found_guard(lambda: service.list_workspaces(user_id=identity.user_id))


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    tags=["workspaces"],
)
def get_workspace(
    workspace_id: str,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> WorkspaceResponse:
    return not_found_guard(
        lambda: service.get_workspace(
            user_id=identity.user_id,
            workspace_id=workspace_id,
        )
    )


@router.post(
    "/workspaces/{workspace_id}/queries",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["queries"],
)
def create_query(
    workspace_id: str,
    body: QueryCreate,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> QueryResponse:
    return not_found_guard(
        lambda: service.create_query(
            user_id=identity.user_id,
            workspace_id=workspace_id,
            question=body.question,
        )
    )


@router.get(
    "/workspaces/{workspace_id}/queries",
    response_model=list[QueryResponse],
    tags=["queries"],
)
def list_queries(
    workspace_id: str,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> list[QueryResponse]:
    return not_found_guard(
        lambda: service.list_queries(
            user_id=identity.user_id,
            workspace_id=workspace_id,
        )
    )


@router.get(
    "/workspaces/{workspace_id}/queries/{query_id}",
    response_model=QueryResponse,
    tags=["queries"],
)
def get_query(
    workspace_id: str,
    query_id: str,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> QueryResponse:
    return not_found_guard(
        lambda: service.get_query(
            user_id=identity.user_id,
            workspace_id=workspace_id,
            query_id=query_id,
        )
    )


@router.post(
    "/workspaces/{workspace_id}/queries/{query_id}/retry",
    response_model=QueryResponse,
    tags=["queries"],
)
def retry_query(
    workspace_id: str,
    query_id: str,
    identity: AuthenticatedIdentity = Depends(current_identity),
    service: Text2SqlWorkspaceService = Depends(get_service),
) -> QueryResponse:
    return not_found_guard(
        lambda: service.retry_query(
            user_id=identity.user_id,
            workspace_id=workspace_id,
            query_id=query_id,
        )
    )
