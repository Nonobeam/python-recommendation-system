import asyncio
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.exception.custom_exceptions import AIProcessingError, GeminiAPIError, MCPValidationError

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


class CommissionExtractionService:
    def __init__(self):
        import logging

        logger = logging.getLogger("recommendation_system.document_service")

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise MCPValidationError("GEMINI_API_KEY environment variable is required")
        logger.info(f"Gemini API key loaded (length: {len(self.api_key)} chars)")

        self.model_name = os.getenv("GEMINI_DOCUMENT_MODEL", "gemini-2.0-flash")
        logger.info(f"Using Gemini model: {self.model_name}")

        self.client = genai.Client(api_key=self.api_key)
        logger.info("Gemini client initialized successfully")
        self.prompt = (
            "You extract structured data from Vietnamese commission contracts.\n"
            "Follow these exact instructions:\n"
            '1. Identify the first clause that contains the phrase ", từ ngày".\n'
            '   - Capture the text that appears before ", từ ngày" in headers "ĐIỀU 2", focus on 2.1. \n'
            '   - Extract the date after "từ ngày" and before "đến ngày". Return as from_date.\n'
            '   - Extract the date after "đến ngày" and before the trailing period. Return as due_date.\n'
            '2. Find the commission clause that states "Bên A ... số tiền hoa hồng".\n'
            "   - Extract the numeric portion of the commission value.\n"
            '   - If the original text contains %, return value_type = "percentage" and remove the % sign.\n'
            '   - If the text is a fixed number (đồng), remove separators (., ,) and return value_type = "fixed_amount".\n'
            "3. Find the payment due date clause (usually mentions between "
            '"Thời hạn thanh toán tiền hoa hồng là" and '
            '"kể từ ngày đầu tiên Khách thuê sử dụng gian hàng theo Hợp đồng thuê").\\n'
            "   - Extract the number of days for payment (must be between 5 and 14 days).\n"
            '   - Return as payment_due_date (just the number, without "ngày" or "days").\n'
            "4. Always return well-formed JSON using this schema:\n"
            "{\n"
            '  "from_date": "dd/MM/yyyy",\n'
            '  "due_date": "dd/MM/yyyy",\n'
            '  "value": "<numeric_string>",\n'
            '  "value_type": "percentage" | "fixed_amount",\n'
            '  "payment_due_date": "<number_of_days>"\n'
            "}\n"
            "Only return the JSON object. Do not include explanations or markdown."
        )

    async def extract_commission_details(self, file_bytes: bytes, mime_type: str) -> Dict[str, str]:
        import logging
        import traceback

        logger = logging.getLogger("recommendation_system.document_service")

        logger.info(
            f"Starting Gemini commission extraction - Model: {self.model_name}, MIME type: {mime_type}, File size: {len(file_bytes)} bytes"
        )

        try:
            logger.debug("Calling Gemini API...")
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime_type), self.prompt],
            )
            logger.info("Gemini API call completed successfully")
        except Exception as exc:
            error_type = type(exc).__name__
            error_msg = str(exc)
            error_trace = traceback.format_exc()
            logger.error(f"Gemini API call failed - Type: {error_type}, Message: {error_msg}")
            logger.debug(f"Full traceback:\n{error_trace}")
            raise GeminiAPIError(
                f"Failed to complete Gemini commission extraction request - {error_type}: {error_msg}"
            ) from exc

        logger.debug("Extracting text from Gemini response...")
        response_text = self._extract_text_from_response(response)
        logger.info(f"Extracted response text (first 200 chars): {response_text[:200]}")

        logger.debug("Parsing extraction result...")
        result = self._parse_extraction_result(response_text)
        logger.info(f"Successfully parsed commission data: {result}")
        return result

    def _extract_text_from_response(self, response: Any) -> str:
        text_content = getattr(response, "text", None)
        if text_content:
            return text_content.strip()
        try:
            candidates = getattr(response, "candidates", [])
            if candidates:
                parts = candidates[0].content.parts
                joined = "".join(part.text for part in parts if hasattr(part, "text"))
                if joined:
                    return joined.strip()
        except Exception as exc:
            raise AIProcessingError("Gemini response missing text content", exc)
        raise AIProcessingError("Gemini response did not include any readable content")

    def _parse_extraction_result(self, content: str) -> Dict[str, str]:
        payload = self._load_json_payload(content)
        required_fields = ("from_date", "due_date", "value", "value_type", "payment_due_date")
        for field in required_fields:
            if not payload.get(field):
                raise AIProcessingError(f"Gemini output missing required field: {field}")

        normalized_value_type = self._normalize_value_type(payload["value_type"], payload["value"])
        normalized_value = self._normalize_value(payload["value"], normalized_value_type)

        return {
            "from_date": str(payload["from_date"]).strip(),
            "due_date": str(payload["due_date"]).strip(),
            "value": normalized_value,
            "value_type": normalized_value_type,
            "payment_due_date": str(payload["payment_due_date"]).strip(),
        }

    def _load_json_payload(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise AIProcessingError("Gemini output did not contain a JSON object")
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise AIProcessingError("Gemini output JSON is malformed", exc)

    def _normalize_value_type(self, value_type: Any, value: Any) -> str:
        vt = str(value_type).strip().lower()
        raw_value = str(value or "")
        if "percent" in vt or "%" in vt:
            return "percentage"
        if "fixed" in vt or "amount" in vt or "currency" in vt or "đồng" in vt:
            return "fixed_amount"
        if "%" in raw_value:
            return "percentage"
        return "fixed_amount"

    def _normalize_value(self, value: Any, value_type: str) -> str:
        raw_value = str(value).strip()
        if not raw_value:
            raise AIProcessingError("Commission value is empty")

        if value_type == "percentage":
            match = re.search(r"-?\d+(?:[.,]\d+)?", raw_value)
            if not match:
                raise AIProcessingError("Unable to extract numeric percentage value")
            numeric = match.group(0).replace(",", ".")
        else:
            numeric = re.sub(r"[^\d-]", "", raw_value)
            if not numeric:
                raise AIProcessingError("Unable to extract numeric fixed amount value")

        try:
            normalized = Decimal(numeric)
        except (InvalidOperation, ValueError) as exc:
            raise AIProcessingError("Commission value is not numeric", exc)

        normalized_str = format(normalized.normalize(), "f")
        return normalized_str.rstrip("0").rstrip(".") if "." in normalized_str else normalized_str
