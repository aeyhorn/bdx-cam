from fastapi import HTTPException, status

from app.core import roles as R
from app.models import Case, User


def ensure_case_readable(user: User, case: Case) -> None:
    if R.can_see_all_cases(user.role.key):
        return
    if case.reporter_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Case not visible")


def ensure_case_writable_production(user: User, case: Case) -> None:
    if user.role.key != R.FEEDBACK_PRODUCTION:
        return
    if case.reporter_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your case")
