from __future__ import annotations


class UserRole:
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    NURSE = "NURSE"
    SENIOR_CARER = "SENIOR_CARER"
    CARER = "CARER"

    ALL = [ADMIN, MANAGER, NURSE, SENIOR_CARER, CARER]
    HIERARCHY = {ADMIN: 5, MANAGER: 4, NURSE: 3, SENIOR_CARER: 2, CARER: 1}
