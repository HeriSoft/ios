"""Quyền theo workspace: trust trước lần Run/Install đầu, tách quyền AI-sửa-file và publish."""
from __future__ import annotations

from enum import Enum

TRUST_WARNING_VI = (
    "Mã nguồn project và các script của dependency (npm install, expo, gradle) có thể thực thi "
    "mã tùy ý với quyền của tài khoản Windows hiện tại.\n\n"
    "• Chỉ tin cậy project do bạn tạo hoặc từ nguồn bạn biết rõ.\n"
    "• Với project lạ, nên chạy trong máy ảo/sandbox riêng.\n"
    "• App Builder AI giảm biến môi trường truyền vào tiến trình con và không truyền API key/GitHub token, "
    "nhưng kiểm tra đường dẫn KHÔNG thay thế sandbox của hệ điều hành."
)
TRUST_WARNING_EN = (
    "Project code and dependency scripts (npm install, expo, gradle) can execute arbitrary code "
    "with your Windows account's permissions.\n\n"
    "• Only trust projects you created or whose source you know.\n"
    "• For unknown projects, use a separate VM/sandbox.\n"
    "• App Builder AI reduces environment variables passed to child processes and never passes API keys/GitHub tokens, "
    "but path checks do NOT replace an OS sandbox."
)


class Capability(str, Enum):
    READ = "read"            # Plan mode: chỉ đọc
    WRITE_WORKSPACE = "write"  # Apply mode: chỉ ghi trong workspace
    RUN_COMMANDS = "run"     # cần workspace trusted
    PUBLISH = "publish"      # GitHub/EAS: luôn xác nhận riêng


def can(capability: Capability, *, trusted: bool, apply_mode: bool = False) -> bool:
    if capability is Capability.READ:
        return True
    if capability is Capability.WRITE_WORKSPACE:
        return apply_mode
    if capability is Capability.RUN_COMMANDS:
        return trusted
    return False  # PUBLISH không bao giờ tự động
