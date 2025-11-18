from fastapi import APIRouter, File, UploadFile

from app.constants import MAX_CONTRACT_FILE_SIZE_BYTES, SUPPORTED_CONTRACT_MIME_TYPES
from app.exception.custom_exceptions import AIProcessingError, GeminiAPIError, MCPValidationError
from app.model.error_code import ErrorCode
from app.model.exception_mapper import map_exception_to_error_code
from app.model.response_helper import error, success
from app.service.document_service import CommissionExtractionService
from app.utils.logger import api_logger

router = APIRouter()

try:
    commission_service = CommissionExtractionService()
except MCPValidationError as exc:
    api_logger.error(f"Commission extraction service initialization failed: {str(exc)}")
    commission_service = None


@router.post(
    "/documents/commission-percentage",
    summary="Extract commission contract terms from uploaded document",
    tags=["Document Intelligence"],
)
async def extract_commission_details(
    contract: UploadFile = File(..., description="Contract PDF containing commission clause"),
):
    if contract.content_type not in SUPPORTED_CONTRACT_MIME_TYPES:
        api_logger.warning(f"Unsupported file type submitted: {contract.content_type}")
        return error(ErrorCode.DOCUMENT_FILE_TYPE_NOT_SUPPORTED, "Only PDF or image files are supported")

    file_bytes = await contract.read()
    if not file_bytes:
        api_logger.warning("Empty file uploaded to commission extraction endpoint")
        return error(ErrorCode.INVALID_REQUEST_PARAMETER, "Uploaded file is empty")

    if len(file_bytes) > MAX_CONTRACT_FILE_SIZE_BYTES:
        api_logger.warning(f"File too large for commission extraction: {len(file_bytes)} bytes")
        return error(ErrorCode.DOCUMENT_FILE_SIZE_LIMIT_EXCEEDED, "File size exceeds 5MB limit")

    if commission_service is None:
        return error(ErrorCode.SERVICE_UNAVAILABLE, "Document processing service is not configured")

    try:
        extraction = await commission_service.extract_commission_details(file_bytes, contract.content_type)
        response_data = {
            "from_date": extraction["from_date"],
            "due_date": extraction["due_date"],
            "value": extraction["value"],
            "value_type": extraction["value_type"],
        }
        return success(response_data)
    except (GeminiAPIError, AIProcessingError) as exc:
        api_logger.error(f"Commission extraction failed: {str(exc)}")
        return error(ErrorCode.GEMINI_API_ERROR, "Unable to extract commission percentage. Try again later.")
    except Exception as exc:
        api_logger.error(f"Unexpected document processing error: {str(exc)}")
        error_code, message = map_exception_to_error_code(exc)
        return error(error_code, message)
