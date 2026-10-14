from fastapi import Depends, HTTPException

from auth import get_current_user  # ADAPT: your existing "current logged-in user" dependency


def get_current_student_id(user=Depends(get_current_user)) -> int:
    """Single place that converts your auth result into a student id."""
    sid = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if sid is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return int(sid)
