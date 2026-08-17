"""解析代理校验逻辑测试。"""

from app.agents.parse_agent import ParseField, validate_parse_result


def _field(status: str, name: str = "金额") -> ParseField:
    return ParseField(
        field_name=name,
        field_value="1" if status == "extracted" else "",
        raw_text="x" if status == "extracted" else "",
        page_no=1,
        extract_status=status,
    )


def test_validate_all_missing():
    """全部字段缺失判为失败。"""
    status, error = validate_parse_result([_field("missing")])
    assert status == "failed"
    assert error


def test_validate_partial_missing():
    """部分字段缺失判为成功。"""
    status, error = validate_parse_result([_field("extracted"), _field("missing")])
    assert status == "success"
    assert error is None
