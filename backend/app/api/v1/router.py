from fastapi import APIRouter

from app.api.v1 import (
    attachments,
    auth,
    cases,
    categories,
    change_requests,
    comments,
    control_systems,
    dashboard,
    knowledge,
    lookup_meta,
    machines,
    post_versions,
    regression_runs,
    roles,
    root_causes,
    test_cases,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(machines.router)
api_router.include_router(control_systems.router)
api_router.include_router(post_versions.router)
api_router.include_router(categories.router)
api_router.include_router(lookup_meta.router)
api_router.include_router(cases.router)
api_router.include_router(comments.router)
api_router.include_router(attachments.router)
api_router.include_router(root_causes.router)
api_router.include_router(change_requests.router)
api_router.include_router(test_cases.router)
api_router.include_router(regression_runs.router)
api_router.include_router(knowledge.router)
api_router.include_router(dashboard.router)
