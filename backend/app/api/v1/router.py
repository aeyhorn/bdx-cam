from fastapi import APIRouter

from app.api.v1 import (
    agent_runs,
    attachments,
    auth,
    cam_step_models,
    cases,
    categories,
    change_requests,
    comments,
    control_systems,
    dashboard,
    knowledge,
    lookup_meta,
    meta,
    machine_post_bindings,
    machines,
    post_versions,
    regression_runs,
    roles,
    root_causes,
    system_builds,
    test_cases,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agent_runs.router)
api_router.include_router(roles.router)
api_router.include_router(machines.router)
api_router.include_router(control_systems.router)
api_router.include_router(post_versions.router)
api_router.include_router(cam_step_models.router)
api_router.include_router(machine_post_bindings.router)
api_router.include_router(categories.router)
api_router.include_router(lookup_meta.router)
api_router.include_router(meta.router)
api_router.include_router(cases.router)
api_router.include_router(comments.router)
api_router.include_router(attachments.router)
api_router.include_router(root_causes.router)
api_router.include_router(change_requests.router)
api_router.include_router(test_cases.router)
api_router.include_router(regression_runs.router)
api_router.include_router(knowledge.router)
api_router.include_router(system_builds.router)
api_router.include_router(dashboard.router)
