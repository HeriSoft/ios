"""Schema dữ liệu chính (Pydantic): ProjectSpec, ChangePlan, ChangeSet."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app_builder.core.workspace import (
    is_valid_android_package,
    is_valid_ios_bundle_id,
    validate_relative_path,
)

Platform = Literal["android", "ios"]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ScreenSpec(BaseModel):
    route: str
    title: str
    description: str = ""


class ThemeSpec(BaseModel):
    style: str = "modern"
    primary: str = "#4F46E5"
    accent: str = "#06B6D4"
    background_light: str = "#F8FAFC"
    background_dark: str = "#0B1120"
    radius: int = 14
    spacing: int = 16
    font_family: str = "System"


class CapabilitySpec(BaseModel):
    """Quyền/chức năng nhạy cảm — mặc định TẮT."""
    login: bool = False
    offline: bool = True
    notifications: bool = False
    camera: bool = False
    location: bool = False


class AIPreferences(BaseModel):
    provider: str = ""
    model: str = ""
    mode: Literal["economy", "balanced", "advanced"] = "economy"
    budget_usd_project: float | None = None
    budget_usd_session: float | None = None


class ProjectSpec(BaseModel):
    schema_version: int = 1
    name: str
    slug: str
    description: str = ""
    language: Literal["vi", "en"] = "vi"
    platforms: list[Platform] = Field(default_factory=lambda: ["android", "ios"])
    android_package: str
    ios_bundle_id: str
    categories: list[str] = Field(default_factory=list)
    template: str = "blank"
    features: list[str] = Field(default_factory=list)
    storage: Literal["local", "sqlite", "none"] = "local"
    backend: Literal["none", "supabase", "firebase", "rest"] = "none"
    capabilities: CapabilitySpec = Field(default_factory=CapabilitySpec)
    ai: AIPreferences = Field(default_factory=AIPreferences)
    main_prompt: str = ""
    references: list[str] = Field(default_factory=list)
    screens: list[ScreenSpec] = Field(default_factory=list)
    navigation: str = "stack"
    data_model: list[dict] = Field(default_factory=list)
    acceptance_tests: list[str] = Field(default_factory=list)
    theme: ThemeSpec = Field(default_factory=ThemeSpec)
    non_goals: list[str] = Field(default_factory=list)
    locked_files: list[str] = Field(default_factory=list)
    approved_requests: list[str] = Field(default_factory=list)
    expo_sdk: str = ""
    created_at: str = Field(default_factory=utcnow_iso)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 60:
            raise ValueError("Tên app phải có 1–60 ký tự")
        return v

    @field_validator("android_package")
    @classmethod
    def _pkg(cls, v: str) -> str:
        if not is_valid_android_package(v):
            raise ValueError("Package ID Android không hợp lệ (vd: com.congty.tenapp)")
        return v

    @field_validator("ios_bundle_id")
    @classmethod
    def _bid(cls, v: str) -> str:
        if not is_valid_ios_bundle_id(v):
            raise ValueError("Bundle ID iOS không hợp lệ (vd: com.congty.tenapp)")
        return v

    @field_validator("platforms")
    @classmethod
    def _platforms(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Chọn ít nhất một nền tảng")
        return sorted(set(v))


# ---- Agent pipeline (dùng từ M3) -------------------------------------------------

class ChangePlan(BaseModel):
    summary: str
    affected_files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    estimated_input_tokens: int | None = None
    estimated_output_tokens: int | None = None


class FileChange(BaseModel):
    operation: Literal["create", "update", "delete"]
    path: str
    expected_sha256: str | None = None
    content: str | None = None
    unified_diff: str | None = None

    @field_validator("path")
    @classmethod
    def _path(cls, v: str) -> str:
        return str(validate_relative_path(v))


class ChangeSet(BaseModel):
    id: str
    summary: str = ""
    changes: list[FileChange]
