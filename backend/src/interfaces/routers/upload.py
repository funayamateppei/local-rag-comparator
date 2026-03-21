"""Upload router - handles document file uploads."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.application.use_cases.document_processor import DocumentProcessorUseCase
from src.domain.models.document import DocumentStatus
from src.interfaces.schemas import ErrorResponse, UploadResponse

router = APIRouter(tags=["upload"])


def get_document_processor_use_case() -> DocumentProcessorUseCase:
    """DI placeholder - overridden in main.py"""
    raise NotImplementedError


@router.post(
    "/api/upload",
    response_model=UploadResponse,
    responses={500: {"model": ErrorResponse}},
    summary="ドキュメントをアップロードして処理する",
    description="PDFまたはテキストファイルをアップロードし、Vector/Graph両方のRAGインデックスに登録する。",
)
async def upload_file(
    file: UploadFile,
    use_case: DocumentProcessorUseCase = Depends(get_document_processor_use_case),
) -> UploadResponse:
    try:
        suffix = Path(file.filename).suffix if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        document = await use_case.execute(tmp_path)

        if document.status == DocumentStatus.FAILED:
            raise HTTPException(status_code=500, detail=document.error or "Processing failed")

        return UploadResponse.from_domain(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
