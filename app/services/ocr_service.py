"""OCR 服务：rapidocr 识别 + 置信度过滤。"""

from dataclasses import dataclass

import numpy as np
from rapidocr_onnxruntime import RapidOCR
from PIL import Image

from app.config import get_settings


@dataclass(slots=True)
class OcrLine:
    """一行 OCR 识别结果。"""

    text: str
    score: float


class OcrService:
    """rapidocr 引擎封装，延迟加载模型。"""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = RapidOCR()
        return self._engine

    def ocr_image(self, source) -> list[OcrLine]:
        """识别图片路径或 numpy 数组，返回识别行。"""
        result, _ = self._get_engine()(source)
        if not result:
            return []
        return [OcrLine(text=str(item[1]), score=float(item[2])) for item in result]


_ocr_service = OcrService()


def ocr_image(source) -> list[OcrLine]:
    """识别图片并返回识别行。"""
    return _ocr_service.ocr_image(source)


def ocr_image_file(file_path: str) -> list[OcrLine]:
    """打开图片文件后 OCR，返回识别行。"""
    image = Image.open(file_path)
    return ocr_image(np.array(image))


def filter_low_confidence(lines: list[OcrLine], threshold: float) -> list[OcrLine]:
    """按 OCR_CONFIDENCE_THRESHOLD 过滤低分识别行。"""
    return [line for line in lines if line.score >= threshold]


def ocr_pdf_page(pdf_page, page_no: int) -> tuple[int, str]:
    """用 PyMuPDF 把 PDF 页渲染为图片后 OCR，返回 (page_no, text)。"""
    pix = pdf_page.get_pixmap(dpi=150)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    lines = filter_low_confidence(ocr_image(np.array(image)), get_settings().ocr_confidence_threshold)
    if not lines:
        raise ValueError(f"PDF 第 {page_no} 页图片无法识别")
    return page_no, "\n".join(line.text for line in lines)
