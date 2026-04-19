ADMIN = "ADMIN"
FEEDBACK_PRODUCTION = "FEEDBACK_PRODUCTION"
ENGINEERING = "ENGINEERING"

ALL_ROLES = (ADMIN, FEEDBACK_PRODUCTION, ENGINEERING)


def can_manage_users(role_key: str) -> bool:
    return role_key == ADMIN


def can_manage_master_data(role_key: str) -> bool:
    return role_key == ADMIN


def can_engineering(role_key: str) -> bool:
    return role_key in (ADMIN, ENGINEERING)


def can_see_all_cases(role_key: str) -> bool:
    return role_key in (ADMIN, ENGINEERING)


def can_internal_comment(role_key: str) -> bool:
    return role_key in (ADMIN, ENGINEERING)


def can_edit_technical_case(role_key: str) -> bool:
    return role_key in (ADMIN, ENGINEERING)
