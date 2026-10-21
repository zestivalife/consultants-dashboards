"""External Diet Plan publication policy."""


def can_publish_independently(*, verification_state: str, experience_years: int | None, plan_status: str, actor_is_author: bool) -> bool:
    return bool(
        verification_state == "VERIFIED"
        and experience_years is not None
        and experience_years >= 1
        and plan_status == "SAVED"
        and actor_is_author
    )
