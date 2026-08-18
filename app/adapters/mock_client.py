"""ApprovalAdapter 的 mock 实现，读取本地样例数据完成闭环演示。"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.adapters.base import (
    ApprovalAdapter,
    ApprovalDetail,
    ApprovalRecord,
    AttachmentInfo,
    DownloadResult,
    WritebackResult,
)


class MockClient(ApprovalAdapter):
    """读取 mock/approvals.json 与 mock/attachments/ 的假审批系统。"""

    def __init__(self, data_dir: str, upload_dir: str):
        self.data_dir = Path(data_dir)
        self.upload_dir = Path(upload_dir)
        approvals_file = self.data_dir / "approvals.json"
        self._items = json.loads(approvals_file.read_text(encoding="utf-8"))["items"]

    def list_pending(self, limit: int) -> list[ApprovalRecord]:
        """返回待办列表。"""
        records = []
        for item in self._items[:limit]:
            records.append(
                ApprovalRecord(
                    approval_code=item["approval_code"],
                    approval_title=item["approval_title"],
                    applicant_name=item["applicant_name"],
                    application_time=datetime.fromisoformat(item["application_time"]),
                    attachment_count=len(item["attachments"]),
                )
            )
        return records

    def get_detail(self, instance_id: str) -> ApprovalDetail:
        """返回审批详情与附件列表。"""
        for item in self._items:
            if item["instance_id"] == instance_id:
                return self._detail_from_item(item)
        raise ValueError(f"审批单不存在: {instance_id}")

    def get_detail_by_code(self, approval_code: str) -> ApprovalDetail:
        """按审批编号定位详情，供拉取链路使用。"""
        for item in self._items:
            if item["approval_code"] == approval_code:
                return self._detail_from_item(item)
        raise ValueError(f"审批单不存在: {approval_code}")

    def _detail_from_item(self, item: dict) -> ApprovalDetail:
        return ApprovalDetail(
            instance_id=item["instance_id"],
            approval_code=item["approval_code"],
            approval_title=item["approval_title"],
            applicant_name=item["applicant_name"],
            application_time=datetime.fromisoformat(item["application_time"]),
            form_data={"source": "mock"},
            attachments=[
                AttachmentInfo(
                    attachment_id=att["attachment_id"],
                    file_name=att["file_name"],
                    file_type=att["file_type"],
                )
                for att in item["attachments"]
            ],
            status=item.get("status", "pending"),
        )

    def download(self, instance_id: str, attachment_id: str, file_name: str) -> DownloadResult:
        """复制样例附件到 uploads，返回路径与校验值。"""
        source = self.data_dir / "attachments" / file_name
        if not source.exists():
            raise FileNotFoundError(f"样例附件不存在: {source}")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        dest = self.upload_dir / f"{instance_id}_{attachment_id}_{file_name}"
        shutil.copy2(source, dest)
        checksum = hashlib.md5(dest.read_bytes()).hexdigest()
        return DownloadResult(file_path=str(dest), file_checksum=checksum)

    def write_comment(self, instance_id: str, review_id: int) -> WritebackResult:
        """写 mock/comments JSON，返回回写结果。"""
        comments_dir = self.data_dir / "comments"
        comments_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "instance_id": instance_id,
            "review_id": review_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        (comments_dir / f"{instance_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return WritebackResult(success=True, response_text="mock writeback ok")
