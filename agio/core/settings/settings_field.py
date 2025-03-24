from pydantic import Field


def ASettingsField(*args, **kwargs):
    return Field(*args, **kwargs)