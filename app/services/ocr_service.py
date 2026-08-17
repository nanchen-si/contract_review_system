"""OCR 服务：rapidocr 识别 + 置信度过滤。"""

from dataclasses import dataclass

from rapidocr_onnxruntime import RapidOCR


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


def filter_low_confidence(lines: list[OcrLine], threshold: float) -> list[OcrLine]:
    """按 OCR_CONFIDENCE_THRESHOLD 过滤低分识别行。"""
    return [line for line in lines if line.score >= threshold]
