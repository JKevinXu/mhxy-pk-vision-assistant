"""Compliance guardrails for proposed features.

This module is intentionally simple for the initial repository scaffold. The
project should reject any feature that tries to reveal hidden game state or
interact with the official game client.
"""

from dataclasses import dataclass

_FORBIDDEN_KEYWORDS = (
    "内存",
    "封包",
    "注入",
    "hook",
    "dll",
    "frida",
    "自动操作",
    "自动战斗",
    "真实血量",
    "对方血量",
    "隐藏信息",
    "绕过反外挂",
)

_ALLOWED_KEYWORDS = (
    "录像",
    "截图",
    "复盘",
    "人工输入",
    "授权",
    "公开可见",
    "训练",
    "估算",
)


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reason: str


def check_feature_scope(description: str) -> ComplianceDecision:
    """Return whether a feature fits the repository's compliance boundary."""
    normalized = description.lower()
    for word in _FORBIDDEN_KEYWORDS:
        if word.lower() in normalized:
            return ComplianceDecision(False, f"包含禁止方向：{word}")

    if any(word.lower() in normalized for word in _ALLOWED_KEYWORDS):
        return ComplianceDecision(True, "属于录像/截图/人工输入/训练复盘等合规方向")

    return ComplianceDecision(
        False,
        "范围不明确：需要明确不读取客户端、不获取隐藏信息、不自动操作游戏",
    )
