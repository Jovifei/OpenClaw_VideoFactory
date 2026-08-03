from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOUL = (ROOT / "SOUL.md").read_text(encoding="utf-8")


def test_status_router_has_an_exact_no_tool_reply_contract() -> None:
    assert "## P0 `/status` 命令守卫" in SOUL
    assert "精确匹配 `/status`" in SOUL
    assert "项目状态：P0 验证进行中；P0-086 的真实同事件去重证据仍待补齐，尚未进入 P1。" in SOUL
    assert "不得调用任何工具、读取或检索工作区、派发子代理" in SOUL


def test_status_router_rejects_all_trailing_text() -> None:
    assert "`/status` 后含任意参数、文字或其他字符时" in SOUL
    assert "只回复：`用法：/status`" in SOUL
