"""Tests for the Automated LLM Inference Harness with Mocking.

Verifies:
1. Mocked end-to-end execution without spending API credits or making network requests.
2. Explicit error raising when credentials are missing (zero silent fallback).
3. Correct prompt construction incorporating SKILL.md and analysis.json.
4. Automatic execution of NumericalClaimValidator against LLM output.
5. Generation of all output artifacts and sanitized metadata (zero credential leakage).
6. Configurable model identifier support from environment variables.
"""

import json
import io
from pathlib import Path
import urllib.error
import pytest
from unittest.mock import patch, MagicMock

from evals.llm_inference import (
    run_llm_inference,
    check_api_credential_status,
    get_configured_model,
    build_llm_prompt,
    call_openrouter_api,
    sanitize_api_key,
    DEFAULT_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    DEFAULT_ANTHROPIC_MODEL,
    OPENROUTER_BASE_URL,
)


class MockAnthropicResponse:
    def __init__(self, content_json_str: str):
        self.content = [MagicMock(type="text", text=content_json_str)]
        self.usage = MagicMock(input_tokens=1420, output_tokens=980)


class MockLLMClient:
    def __init__(self, response_dict: dict):
        self.response_dict = response_dict

    def create_message(self, prompt: str, model: str):
        return {
            "content": json.dumps(self.response_dict),
            "usage": {"input_tokens": 1500, "output_tokens": 1200},
        }


@pytest.fixture
def test_paths(tmp_path):
    repo_dir = Path(__file__).resolve().parent.parent
    analysis_path = repo_dir / "results" / "analysis.json"
    skill_path = repo_dir / ".claude" / "skills" / "monthly-trend-analysis" / "SKILL.md"
    if not skill_path.exists():
        skill_path = repo_dir.parent / ".claude" / "skills" / "monthly-trend-analysis" / "SKILL.md"
    return analysis_path, skill_path, tmp_path


def test_missing_credentials_raises_explicit_error(test_paths, monkeypatch):
    analysis_path, skill_path, tmp_dir = test_paths
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Must raise RuntimeError and not pretend LLM succeeded
    with pytest.raises(RuntimeError) as exc_info:
        run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=tmp_dir,
        )
    assert "ANTHROPIC_API_KEY is MISSING" in str(exc_info.value)


def test_dry_run_mode(test_paths, monkeypatch):
    analysis_path, skill_path, tmp_dir = test_paths
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    res = run_llm_inference(
        analysis_path=analysis_path,
        skill_path=skill_path,
        output_dir=tmp_dir,
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN"
    assert res["credential_status"] == "MISSING"
    assert res["model"] == DEFAULT_MODEL


def test_mocked_llm_inference_end_to_end(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    mock_llm_response = {
        "executive_summary": (
            "# Executive Financial Review\n\n"
            "January 2025 revenue stood at $167,587.50. "
            "In December 2025, reported operating income of +$534,551.41 was distorted by "
            "a -$1,244,429.84 tax benefit credit. Normalized operating loss was -$381,241.27."
        ),
        "financial_claims": [
            {
                "claim_text": "January 2025 revenue stood at $167,587.50.",
                "metric": "revenue",
                "period": "2025-01",
                "claimed_value": 167587.50,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Reported operating income of +$534,551.41 in Dec 2025.",
                "metric": "operating_income",
                "period": "2025-12",
                "claimed_value": 534551.41,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Non-recurring tax benefit credit of -$1,244,429.84.",
                "metric": "tax_benefit",
                "period": "2025-12",
                "claimed_value": -1244429.84,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Normalized operating loss was -$381,241.27.",
                "metric": "normalized_operating_income",
                "period": "2025-12",
                "claimed_value": -381241.27,
                "claimed_unit": "currency",
            },
        ],
    }

    mock_client = MockLLMClient(mock_llm_response)

    res = run_llm_inference(
        analysis_path=analysis_path,
        skill_path=skill_path,
        output_dir=tmp_dir,
        mock_client=mock_client,
    )

    assert res["status"] == "SUCCESS"
    assert res["is_live_call"] is False

    # Check validation summary
    val_summary = res["validation_summary"]
    assert val_summary["total_claims"] == 4
    assert val_summary["verified_claims"] == 4
    assert val_summary["invalid_claims"] == 0
    assert val_summary["accuracy_rate_pct"] == 100.0

    # Verify generated artifact files exist
    assert (tmp_dir / "llm_commentary.md").exists()
    assert (tmp_dir / "llm_analysis_output.json").exists()
    assert (tmp_dir / "llm_validation_result.json").exists()
    assert (tmp_dir / "llm_validation_report.md").exists()
    assert (tmp_dir / "llm_run_metadata.json").exists()

    # Verify metadata is clean and contains zero secrets
    with open(tmp_dir / "llm_run_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["is_live_call"] is False
    assert "api_key" not in meta
    assert "secret" not in json.dumps(meta).lower()
    assert meta["validation_summary"]["verified_claims"] == 4


def test_anthropic_api_call_parameters_and_execution(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    mock_llm_payload = {
        "executive_summary": (
            "# Executive Financial Review via Anthropic\n\n"
            "January 2025 revenue stood at $167,587.50. "
            "In December 2025, reported operating income was $534,551.41 with a non-recurring "
            "tax benefit credit of -$1,244,429.84. Normalized operating income was -$381,241.27."
        ),
        "financial_claims": [
            {
                "claim_text": "January 2025 revenue stood at $167,587.50.",
                "metric": "revenue",
                "period": "2025-01",
                "claimed_value": 167587.50,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Reported operating income of $534,551.41 in Dec 2025.",
                "metric": "operating_income",
                "period": "2025-12",
                "claimed_value": 534551.41,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Non-recurring tax benefit credit of -$1,244,429.84.",
                "metric": "tax_benefit",
                "period": "2025-12",
                "claimed_value": -1244429.84,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Normalized operating loss was -$381,241.27.",
                "metric": "normalized_operating_income",
                "period": "2025-12",
                "claimed_value": -381241.27,
                "claimed_unit": "currency",
            },
        ],
    }

    mock_msg = MockAnthropicResponse(json.dumps(mock_llm_payload))
    mock_messages_api = MagicMock()
    mock_messages_api.create.return_value = mock_msg
    mock_client = MagicMock()
    mock_client.messages = mock_messages_api

    with patch("anthropic.Anthropic", return_value=mock_client) as mock_anthropic_class:
        res = run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=tmp_dir,
            provider="anthropic",
            api_key="mock-anthropic-key-value",
        )

    # 1. Verify Anthropic client instantiation
    mock_anthropic_class.assert_called_once_with(api_key="mock-anthropic-key-value")

    # 2. Verify messages.create invocation parameters
    mock_messages_api.create.assert_called_once()
    call_kwargs = mock_messages_api.create.call_args.kwargs

    # Crucial assertion: temperature must NOT be passed to messages.create in SDK v1.0+
    assert "temperature" not in call_kwargs, (
        "Anthropic SDK v1.0+ removed the 'temperature' parameter; passing it causes a TypeError"
    )
    assert call_kwargs["model"] == DEFAULT_ANTHROPIC_MODEL
    assert call_kwargs["max_tokens"] == 4096
    assert isinstance(call_kwargs["messages"], list)
    assert call_kwargs["messages"][0]["role"] == "user"

    # 3. Parameter compatibility check against installed SDK signature
    import anthropic
    import inspect
    sig = inspect.signature(anthropic.resources.Messages.create)
    sig.bind_partial(**call_kwargs)

    # 4. Verify inference output and validation
    assert res["status"] == "SUCCESS"
    assert res["is_live_call"] is True
    assert res["provider"] == "anthropic"
    assert res["model"] == DEFAULT_ANTHROPIC_MODEL
    assert res["validation_summary"]["verified_claims"] == 4
    assert res["validation_summary"]["invalid_claims"] == 0
    assert res["validation_summary"]["accuracy_rate_pct"] == 100.0

    # 5. Verify all artifact files were saved
    assert (tmp_dir / "llm_commentary.md").exists()
    assert (tmp_dir / "llm_analysis_output.json").exists()
    assert (tmp_dir / "llm_validation_result.json").exists()
    assert (tmp_dir / "llm_validation_report.md").exists()
    assert (tmp_dir / "llm_run_metadata.json").exists()

    # 6. Verify zero secret leakage in metadata
    with open(tmp_dir / "llm_run_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["is_live_call"] is True
    assert meta["provider"] == "anthropic"
    assert meta["token_usage"]["input_tokens"] == 1420
    assert meta["token_usage"]["output_tokens"] == 980
    assert "mock-anthropic-key-value" not in json.dumps(meta)
    assert "api_key" not in meta


def test_anthropic_api_error_handling(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    mock_messages_api = MagicMock()
    mock_messages_api.create.side_effect = Exception("Anthropic API rate limit exceeded")
    mock_client = MagicMock()
    mock_client.messages = mock_messages_api

    with patch("anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            run_llm_inference(
                analysis_path=analysis_path,
                skill_path=skill_path,
                output_dir=tmp_dir,
                provider="anthropic",
                api_key="mock-key-12345",
            )
    assert "Live Anthropic API execution failed: Anthropic API rate limit exceeded" in str(exc_info.value)
    assert "mock-key-12345" not in str(exc_info.value)


def test_configurable_model_identifier(monkeypatch):
    custom_model = "claude-3-7-sonnet-20250219"
    monkeypatch.setenv("ANTHROPIC_MODEL", custom_model)
    assert get_configured_model() == custom_model


def test_invalid_json_from_llm_raises_error(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    class CorruptedLLMClient:
        def create_message(self, prompt: str, model: str):
            return {"content": "This is not JSON at all"}

    with pytest.raises(ValueError) as exc_info:
        run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=tmp_dir,
            mock_client=CorruptedLLMClient(),
        )
    assert "Failed to parse structured JSON" in str(exc_info.value)


class MockUrllibResponse:
    """Mock urllib context manager for HTTP responses."""

    def __init__(self, data_dict: dict, status: int = 200):
        self._raw_bytes = json.dumps(data_dict).encode("utf-8")
        self.status = status

    def read(self):
        return self._raw_bytes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_openrouter_missing_credentials_raises_error(test_paths, monkeypatch):
    analysis_path, skill_path, tmp_dir = test_paths
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=tmp_dir,
            provider="openrouter",
        )
    assert "OPENROUTER_API_KEY is MISSING in environment" in str(exc_info.value)


def test_openrouter_configurable_model(monkeypatch):
    assert get_configured_model("openrouter") == DEFAULT_OPENROUTER_MODEL
    assert DEFAULT_OPENROUTER_MODEL == "anthropic/claude-sonnet-4.5"

    custom_model = "meta-llama/llama-3.3-70b-instruct:free"
    monkeypatch.setenv("OPENROUTER_MODEL", custom_model)
    assert get_configured_model("openrouter") == custom_model


def test_openrouter_dry_run_mode(test_paths, monkeypatch):
    analysis_path, skill_path, tmp_dir = test_paths
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    res = run_llm_inference(
        analysis_path=analysis_path,
        skill_path=skill_path,
        output_dir=tmp_dir,
        provider="openrouter",
        dry_run=True,
    )
    assert res["status"] == "DRY_RUN"
    assert res["provider"] == "openrouter"
    assert res["credential_status"] == "MISSING"
    assert res["model"] == DEFAULT_OPENROUTER_MODEL


def test_mocked_openrouter_inference_end_to_end_and_numerical_validation(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    mock_llm_payload = {
        "executive_summary": (
            "# Executive Financial Review via OpenRouter\n\n"
            "January 2025 revenue stood at $167,587.50. "
            "In December 2025, reported operating income was $534,551.41 with a non-recurring "
            "tax benefit credit of -$1,244,429.84. Normalized operating income was -$381,241.27."
        ),
        "financial_claims": [
            {
                "claim_text": "January 2025 revenue stood at $167,587.50.",
                "metric": "revenue",
                "period": "2025-01",
                "claimed_value": 167587.50,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Reported operating income of $534,551.41 in Dec 2025.",
                "metric": "operating_income",
                "period": "2025-12",
                "claimed_value": 534551.41,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Non-recurring tax benefit credit of -$1,244,429.84.",
                "metric": "tax_benefit",
                "period": "2025-12",
                "claimed_value": -1244429.84,
                "claimed_unit": "currency",
            },
            {
                "claim_text": "Normalized operating loss was -$381,241.27.",
                "metric": "normalized_operating_income",
                "period": "2025-12",
                "claimed_value": -381241.27,
                "claimed_unit": "currency",
            },
        ],
    }

    mock_msg = MockAnthropicResponse(json.dumps(mock_llm_payload))
    mock_messages_api = MagicMock()
    mock_messages_api.create.return_value = mock_msg
    mock_client = MagicMock()
    mock_client.messages = mock_messages_api

    with patch("anthropic.Anthropic", return_value=mock_client) as mock_anthropic_class:
        res = run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=tmp_dir,
            provider="openrouter",
            api_key="mock-openrouter-key",
        )

    # 1. Verify Anthropic client instantiation using OpenRouter's Anthropic-compatible endpoint
    mock_anthropic_class.assert_called_once()
    init_kwargs = mock_anthropic_class.call_args.kwargs
    assert init_kwargs["base_url"] == OPENROUTER_BASE_URL
    assert init_kwargs["api_key"] is None
    assert init_kwargs["auth_token"] == "mock-openrouter-key"
    assert init_kwargs["default_headers"]["Authorization"] == "Bearer mock-openrouter-key"
    assert "HTTP-Referer" in init_kwargs["default_headers"]
    assert "X-Title" in init_kwargs["default_headers"]

    # 2. Verify messages.create invocation parameters
    mock_messages_api.create.assert_called_once()
    call_kwargs = mock_messages_api.create.call_args.kwargs
    assert "temperature" not in call_kwargs
    assert call_kwargs["model"] == DEFAULT_OPENROUTER_MODEL
    assert call_kwargs["max_tokens"] == 4096
    assert isinstance(call_kwargs["messages"], list)
    assert call_kwargs["extra_headers"]["Authorization"] == "Bearer mock-openrouter-key"

    # 3. Verify output status and numerical validation
    assert res["status"] == "SUCCESS"
    assert res["is_live_call"] is True
    assert res["provider"] == "openrouter"
    assert res["model"] == DEFAULT_OPENROUTER_MODEL

    val_summary = res["validation_summary"]
    assert val_summary["total_claims"] == 4
    assert val_summary["verified_claims"] == 4
    assert val_summary["invalid_claims"] == 0
    assert val_summary["accuracy_rate_pct"] == 100.0

    # 4. Verify generated artifact files exist
    assert (tmp_dir / "llm_commentary.md").exists()
    assert (tmp_dir / "llm_analysis_output.json").exists()
    assert (tmp_dir / "llm_validation_result.json").exists()
    assert (tmp_dir / "llm_validation_report.md").exists()
    assert (tmp_dir / "llm_run_metadata.json").exists()

    # 5. Verify metadata contains provider info and zero secrets
    with open(tmp_dir / "llm_run_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["provider"] == "openrouter"
    assert meta["model"] == DEFAULT_OPENROUTER_MODEL
    assert meta["is_live_call"] is True
    assert meta["token_usage"]["input_tokens"] == 1420
    assert meta["token_usage"]["output_tokens"] == 980
    assert "api_key" not in meta
    assert "secret" not in json.dumps(meta).lower()
    assert "mock-openrouter-key" not in json.dumps(meta)


def test_openrouter_anthropic_error_handling(test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    mock_messages_api = MagicMock()
    mock_messages_api.create.side_effect = Exception("User credit balance exhausted")
    mock_client = MagicMock()
    mock_client.messages = mock_messages_api

    with patch("anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            run_llm_inference(
                analysis_path=analysis_path,
                skill_path=skill_path,
                output_dir=tmp_dir,
                provider="openrouter",
                api_key="mock-key-secret-999",
            )
    assert "Live OpenRouter API execution failed: User credit balance exhausted" in str(exc_info.value)
    assert "mock-key-secret-999" not in str(exc_info.value)


def test_openrouter_api_http_error_handling():
    mock_error_fp = io.BytesIO(b'{"error": {"message": "Invalid credentials provided"}}')
    http_error = urllib.error.HTTPError(
        url="https://openrouter.ai/api/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=mock_error_fp,
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(RuntimeError) as exc_info:
            call_openrouter_api(
                prompt="test prompt",
                model="anthropic/claude-sonnet-4.5",
                api_key="invalid-key-secret",
            )
    assert "Live OpenRouter API execution failed (HTTP 401)" in str(exc_info.value)
    assert "invalid-key-secret" not in str(exc_info.value)


def test_openrouter_api_structured_error_response():
    error_response = {
        "error": {
            "message": "User has exceeded rate limits.",
            "code": 429,
        }
    }
    with patch("urllib.request.urlopen", return_value=MockUrllibResponse(error_response)):
        with pytest.raises(RuntimeError) as exc_info:
            call_openrouter_api(
                prompt="test prompt",
                model="anthropic/claude-sonnet-4.5",
                api_key="test-key",
            )
    assert "OpenRouter API returned error: User has exceeded rate limits." in str(exc_info.value)


def test_provider_selection_logic(monkeypatch, test_paths):
    analysis_path, skill_path, tmp_dir = test_paths

    # 1. Explicit provider argument takes highest precedence
    res = run_llm_inference(analysis_path, skill_path, tmp_dir, provider="openrouter", dry_run=True)
    assert res["provider"] == "openrouter"

    res = run_llm_inference(analysis_path, skill_path, tmp_dir, provider="anthropic", dry_run=True)
    assert res["provider"] == "anthropic"

    # 2. LLM_PROVIDER env variable takes precedence when provider is omitted
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    res = run_llm_inference(analysis_path, skill_path, tmp_dir, dry_run=True)
    assert res["provider"] == "openrouter"

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    res = run_llm_inference(analysis_path, skill_path, tmp_dir, dry_run=True)
    assert res["provider"] == "anthropic"

    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    # 3. Auto-detection: OPENROUTER_API_KEY present and ANTHROPIC_API_KEY missing -> openrouter
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-mock-test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = run_llm_inference(analysis_path, skill_path, tmp_dir, dry_run=True)
    assert res["provider"] == "openrouter"

    # 4. Auto-detection: ANTHROPIC_API_KEY present -> anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-mock-test-key")
    res = run_llm_inference(analysis_path, skill_path, tmp_dir, dry_run=True)
    assert res["provider"] == "anthropic"


def test_sanitize_api_key():
    assert sanitize_api_key("sk-or-v1-normal") == "sk-or-v1-normal"
    assert sanitize_api_key('  "sk-or-v1-quoted"  ') == "sk-or-v1-quoted"
    assert sanitize_api_key("  'sk-or-v1-single-quoted'  ") == "sk-or-v1-single-quoted"
    # Strips control characters like \x16 (^V), newlines, and carriage returns
    assert sanitize_api_key("\x16\r\n\nsk-or-v1-with-control\n") == "sk-or-v1-with-control"
    assert sanitize_api_key(None) is None
    assert sanitize_api_key("") is None
    assert sanitize_api_key("   ") is None
    assert sanitize_api_key("tiny") is None  # < 6 chars


def test_openrouter_wire_headers_send_bearer():
    """Verify that Anthropic client configured for OpenRouter formats Authorization: Bearer on the wire."""
    import anthropic
    mock_key = "sk-or-v1-mock-test-key-555"
    client = anthropic.Anthropic(
        base_url=OPENROUTER_BASE_URL,
        api_key=None,
        auth_token=mock_key,
        default_headers={
            "Authorization": f"Bearer {mock_key}",
            "HTTP-Referer": "https://github.com/RE-Financial-AI-Assignment",
            "X-Title": "RE Financial Analysis Tool",
        },
    )
    req = client._build_request(anthropic._base_client.FinalRequestOptions.construct(
        method="post",
        url="/v1/messages",
        headers={"Authorization": f"Bearer {mock_key}"},
        json_data={"model": "test", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
    ))
    assert str(req.url) == "https://openrouter.ai/api/v1/messages"
    assert req.headers.get("authorization") == f"Bearer {mock_key}"
    assert "x-api-key" not in req.headers
    assert req.headers.get("http-referer") == "https://github.com/RE-Financial-AI-Assignment"
    assert req.headers.get("x-title") == "RE Financial Analysis Tool"

