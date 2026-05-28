APPLY_MODE_SEMI = "semi_auto"
APPLY_MODE_AUTO = "auto"

VALID_APPLY_MODES = {APPLY_MODE_SEMI, APPLY_MODE_AUTO}


def sync_apply_mode_flags(profile) -> None:
    """Синхронизирует apply_mode и legacy auto_apply_enabled."""
    if profile.apply_mode == APPLY_MODE_AUTO:
        profile.auto_apply_enabled = True
    else:
        profile.apply_mode = APPLY_MODE_SEMI
        profile.auto_apply_enabled = False


def set_apply_mode(profile, mode: str) -> None:
    if mode not in VALID_APPLY_MODES:
        raise ValueError(f"Invalid apply mode: {mode}")
    profile.apply_mode = mode
    sync_apply_mode_flags(profile)
