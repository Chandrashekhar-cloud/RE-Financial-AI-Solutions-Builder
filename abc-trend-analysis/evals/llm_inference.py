"""Automated LLM Inference & Financial Commentary Pipeline.

Orchestrates real LLM analysis of financial datasets:
1. Supports Anthropic API and OpenRouter (OpenAI-compatible) API.
2. Loads authoritative analysis.json and skill guidelines (SKILL.md).
3. Requests structured executive review and machine-readable financial claims.
4. Automatically validates numerical claims with NumericalClaimValidator.
5. Saves verified commentary, validation audit, and sanitized run metadata.
6. Strictly prevents false claims of live execution when API credentials are absent.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Dict, Any, Optional, Tuple
import urllib.error
import urllib.request

from .numerical_validator import NumericalClaimValidator


OPENROUTER_BASE_URL = "https://openrouter.ai/api"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-sonnet-4.5"
DEFAULT_MODEL = DEFAULT_ANTHROPIC_MODEL


def sanitize_api_key(raw_key: Optional[str]) -> Optional[str]:
    """Sanitize API key by stripping quotes, whitespace, and non-printable control characters."""
    if not raw_key:
        return None
    cleaned = raw_key.strip().strip("'\"").strip()
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() and not ch.isspace())
    return cleaned if len(cleaned) > 5 else None


def get_configured_model(provider: str = "anthropic") -> str:
    """Retrieve configurable model identifier from environment variable based on provider."""
    provider_clean = (provider or "anthropic").strip().lower()
    if provider_clean == "openrouter":
        return os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)


def check_api_credential_status(provider: str = "anthropic") -> Tuple[bool, str]:
    """Check if API credentials for the requested provider are present without logging value."""
    provider_clean = (provider or "anthropic").strip().lower()
    if provider_clean == "openrouter":
        key = sanitize_api_key(os.environ.get("OPENROUTER_API_KEY"))
    else:
        key = sanitize_api_key(os.environ.get("ANTHROPIC_API_KEY"))
    if key and len(key) > 5:
        return True, "PRESENT"
    return False, "MISSING"


def call_openrouter_api(
    prompt: str,
    model: str,
    api_key: str,
    api_url: str = OPENROUTER_API_URL,
    timeout: int = 90,
) -> Tuple[str, Dict[str, int]]:
    """Execute chat completion request to OpenRouter's OpenAI-compatible API.

    Returns:
        Tuple of (response_content_string, normalized_token_usage_dict)
    """
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.0,
        "max_tokens": 4096,
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=req_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/RE-Financial-AI-Assignment",
            "X-Title": "RE Financial Analysis Tool",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_bytes = resp.read()
            resp_json = json.loads(resp_bytes.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Live OpenRouter API execution failed (HTTP {exc.code}): {err_body}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Live OpenRouter API execution network error: {exc.reason}")
    except Exception as exc:
        raise RuntimeError(f"Live OpenRouter API execution failed: {exc}")

    choices = resp_json.get("choices")
    if not choices or not isinstance(choices, list):
        if "error" in resp_json:
            err_detail = resp_json["error"].get("message", json.dumps(resp_json["error"]))
            raise RuntimeError(f"OpenRouter API returned error: {err_detail}")
        raise ValueError(f"Unexpected response structure from OpenRouter: {resp_json}")

    first_choice = choices[0]
    message = first_choice.get("message", {})
    content = message.get("content", "")

    usage = resp_json.get("usage", {})
    token_usage = {
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }

    return content, token_usage


def build_llm_prompt(analysis_data: Dict[str, Any], skill_instructions: str) -> str:
    """Construct the system prompt and payload for financial analysis."""
    # Provide concise schema representation to keep prompt focused
    summarized_data = {
        "metadata": analysis_data.get("metadata", {}),
        "monthly_summaries": analysis_data.get("monthly_summaries", []),
        "ttm_windows": [w for w in analysis_data.get("ttm_windows", []) if w.get("is_valid")],
        "anomalies_and_flags": analysis_data.get("anomalies_and_flags", []),
        "baseline_comparison": analysis_data.get("baseline_comparison", {}),
    }

    prompt = f"""You are an expert Fractional CFO and FP&A advisor analyzing financial performance.
Strictly adhere to the following analytical skill protocol:

=== SKILL PROTOCOL (SKILL.md) ===
{skill_instructions}

=== FACTUAL SOURCE OF TRUTH (analysis.json) ===
{json.dumps(summarized_data, indent=2)}

=== OUTPUT INSTRUCTIONS ===
You must return a valid JSON object with EXACTLY two top-level keys:
1. "executive_summary": A detailed, professional markdown financial report following the Standard Output Format (Sections A through G).
2. "financial_claims": A list of every single key financial number and percentage cited in your review, formatted as:
   [
     {{
       "claim_text": "Sentence or bullet point citing the figure",
       "metric": "revenue | gross_profit | gross_margin_pct | total_opex | operating_income | normalized_operating_income | tax_benefit | stock_based_compensation",
       "period": "YYYY-MM or formatted period",
       "claimed_value": numeric_value,
       "claimed_unit": "currency | percent",
       "is_ttm": boolean
     }}
   ]

Return ONLY raw valid JSON. Do not wrap in backticks or markdown formatting.
"""
    return prompt


def run_llm_inference(
    analysis_path: Path,
    skill_path: Path,
    output_dir: Path,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    mock_client: Optional[Any] = None,
    dry_run: bool = False,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute LLM inference or mock verification.

    Supports both native Anthropic and OpenRouter (OpenAI-compatible) providers.
    Returns dict containing execution status, generated paths, and validation metrics.
    Raises RuntimeError if live run requested without valid API credentials.
    """
    resolved_provider = (
        provider
        or os.environ.get("LLM_PROVIDER")
        or ("openrouter" if os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY") else "anthropic")
    ).strip().lower()

    model_name = model or get_configured_model(resolved_provider)
    is_present, cred_status = check_api_credential_status(resolved_provider)

    # Load factual data
    if not analysis_path.exists():
        raise FileNotFoundError(f"analysis.json not found at: {analysis_path}")
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis_data = json.load(f)

    # Load skill
    if not skill_path.exists():
        raise FileNotFoundError(f"SKILL.md not found at: {skill_path}")
    with open(skill_path, "r", encoding="utf-8") as f:
        skill_text = f.read()

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Check credential availability
    key_env_var = "OPENROUTER_API_KEY" if resolved_provider == "openrouter" else "ANTHROPIC_API_KEY"
    raw_key = api_key or os.environ.get(key_env_var)
    effective_key = sanitize_api_key(raw_key)
    if not effective_key and not mock_client and not dry_run:
        raise RuntimeError(
            f"{key_env_var} is MISSING in environment. "
            "Real automated LLM inference cannot execute without credentials. "
            f"Use mock client for automated testing or set {key_env_var}."
        )

    # 1. Perform inference (Mock, Dry-Run, or Live)
    prompt_content = build_llm_prompt(analysis_data, skill_text)
    response_text = ""
    token_usage = {}
    is_live_call = False

    if mock_client is not None:
        # Mocked execution for reliable test harness
        mock_res = mock_client.create_message(prompt=prompt_content, model=model_name)
        response_text = mock_res.get("content", "")
        token_usage = mock_res.get("usage", {"input_tokens": 1250, "output_tokens": 1500})
        is_live_call = False
    elif dry_run:
        return {
            "status": "DRY_RUN",
            "message": "Prompt prepared successfully. Inference not dispatched.",
            "provider": resolved_provider,
            "credential_status": cred_status,
            "model": model_name,
        }
    else:
        # Live LLM Inference via Anthropic or OpenRouter (Anthropic-compatible endpoint)
        try:
            import anthropic

            if resolved_provider == "openrouter":
                base_url = os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL)
                client = anthropic.Anthropic(
                    base_url=base_url,
                    api_key=None,
                    auth_token=effective_key,
                    default_headers={
                        "Authorization": f"Bearer {effective_key}",
                        "HTTP-Referer": "https://github.com/RE-Financial-AI-Assignment",
                        "X-Title": "RE Financial Analysis Tool",
                    },
                )
                create_kwargs: Dict[str, Any] = {
                    "model": model_name,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt_content}],
                    "extra_headers": {
                        "Authorization": f"Bearer {effective_key}",
                        "HTTP-Referer": "https://github.com/RE-Financial-AI-Assignment",
                        "X-Title": "RE Financial Analysis Tool",
                    },
                }
                message = client.messages.create(**create_kwargs)
            else:
                client = anthropic.Anthropic(api_key=effective_key)
                message = client.messages.create(
                    model=model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt_content}],
                )
            is_live_call = True
            response_text = "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            )
            token_usage = {
                "input_tokens": getattr(message.usage, "input_tokens", 0),
                "output_tokens": getattr(message.usage, "output_tokens", 0),
            }
        except Exception as exc:
            provider_title = "OpenRouter" if resolved_provider == "openrouter" else "Anthropic"
            raise RuntimeError(f"Live {provider_title} API execution failed: {exc}")

    # 2. Parse LLM JSON Output
    cleaned_json_text = response_text.strip()
    if cleaned_json_text.startswith("```json"):
        cleaned_json_text = cleaned_json_text[7:]
    if cleaned_json_text.startswith("```"):
        cleaned_json_text = cleaned_json_text[3:]
    if cleaned_json_text.endswith("```"):
        cleaned_json_text = cleaned_json_text[:-3]
    cleaned_json_text = cleaned_json_text.strip()

    try:
        parsed_output = json.loads(cleaned_json_text)
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to parse structured JSON from LLM response: {err}\nResponse was:\n{response_text[:300]}...")

    executive_summary = parsed_output.get("executive_summary", "")
    claims = parsed_output.get("financial_claims", [])

    # 3. Deterministic Numerical Grounding Validation
    validator = NumericalClaimValidator(analysis_data)
    validation_results = validator.validate_claims(claims, commentary_text=executive_summary)
    validation_report_md = validator.generate_markdown_report(validation_results)

    # 4. Save Artifacts
    out_commentary = output_dir / "llm_commentary.md"
    out_json = output_dir / "llm_analysis_output.json"
    out_val_json = output_dir / "llm_validation_result.json"
    out_val_report = output_dir / "llm_validation_report.md"
    out_metadata = output_dir / "llm_run_metadata.json"

    with open(out_commentary, "w", encoding="utf-8") as f:
        f.write(executive_summary)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(parsed_output, f, indent=2)

    with open(out_val_json, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2)

    with open(out_val_report, "w", encoding="utf-8") as f:
        f.write(validation_report_md)

    run_meta = {
        "timestamp_utc": timestamp,
        "provider": resolved_provider,
        "model": model_name,
        "is_live_call": is_live_call,
        "api_credential_status": cred_status,
        "token_usage": token_usage,
        "validation_summary": validation_results.get("summary", {}),
        "artifacts": {
            "commentary_markdown": str(out_commentary.name),
            "structured_output_json": str(out_json.name),
            "validation_results_json": str(out_val_json.name),
            "validation_report_markdown": str(out_val_report.name),
        },
    }
    with open(out_metadata, "w", encoding="utf-8") as f:
        json.dump(run_meta, f, indent=2)

    return {
        "status": "SUCCESS",
        "is_live_call": is_live_call,
        "provider": resolved_provider,
        "model": model_name,
        "validation_summary": validation_results.get("summary", {}),
        "commentary_path": out_commentary,
        "validation_json_path": out_val_json,
        "validation_report_md_path": out_val_report,
        "metadata_path": out_metadata,
    }


def main(argv=None) -> int:
    """CLI entrypoint for automated LLM financial review and validation."""
    import argparse
    parser = argparse.ArgumentParser(description="Run automated LLM financial review with numerical grounding.")
    parser.add_argument("--analysis", default="results/analysis.json", help="Path to analysis.json")
    parser.add_argument("--skill", default="../.claude/skills/monthly-trend-analysis/SKILL.md", help="Path to SKILL.md")
    parser.add_argument("--output-dir", default="results", help="Directory for output artifacts")
    parser.add_argument("--provider", choices=["anthropic", "openrouter"], default=None, help="LLM provider (anthropic or openrouter)")
    parser.add_argument("--model", default=None, help="Model override (e.g. claude-3-5-sonnet-20241022 or openrouter/free)")
    parser.add_argument("--dry-run", action="store_true", help="Prepare prompt and inspect credential status without calling API")
    args = parser.parse_args(argv)

    repo_dir = Path(__file__).resolve().parent.parent
    analysis_path = (repo_dir / args.analysis).resolve()
    skill_path = (repo_dir / args.skill).resolve()
    if not skill_path.exists():
        # Fallback to local .claude skill
        skill_path = repo_dir / ".claude/skills/monthly-trend-analysis/SKILL.md"

    out_dir = (repo_dir / args.output_dir).resolve()

    resolved_provider = (
        args.provider
        or os.environ.get("LLM_PROVIDER")
        or ("openrouter" if os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY") else "anthropic")
    ).strip().lower()

    configured_model = args.model or get_configured_model(resolved_provider)
    is_present, cred_status = check_api_credential_status(resolved_provider)

    endpoint_display = (
        os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL)
        if resolved_provider == "openrouter"
        else "https://api.anthropic.com (default)"
    )

    print("==================================================================")
    print("RE Financial Services — Automated LLM Financial Review Harness")
    print("==================================================================")
    print(f"LLM Provider:                   {resolved_provider}")
    print(f"API Credential Status:          {cred_status}")
    print(f"Configured Model Identifier:    {configured_model}")
    print(f"Endpoint:                       {endpoint_display}")

    if not is_present and not args.dry_run:
        key_var = "OPENROUTER_API_KEY" if resolved_provider == "openrouter" else "ANTHROPIC_API_KEY"
        print(f"\nERROR: {key_var} environment variable is MISSING.", file=sys.stderr)
        print(f"To run live automated LLM inference with {resolved_provider}, configure {key_var} in your local environment.", file=sys.stderr)
        print("Offline deterministic pipeline remains fully operational (python scripts/run_pipeline.py --offline).", file=sys.stderr)
        return 1

    try:
        res = run_llm_inference(
            analysis_path=analysis_path,
            skill_path=skill_path,
            output_dir=out_dir,
            provider=resolved_provider,
            model=args.model,
            dry_run=args.dry_run,
        )
        print(f"\nExecution Status: {res.get('status')}")
        if res.get("status") == "SUCCESS":
            val_sum = res.get("validation_summary", {})
            print(f"Total Claims Evaluated: {val_sum.get('total_claims')}")
            print(f"Verified Claims:        {val_sum.get('verified_claims')}")
            print(f"Invalid Discrepancies:  {val_sum.get('invalid_claims')}")
            print(f"Numerical Accuracy:     {val_sum.get('accuracy_rate_pct')}%")
            print(f"Numerical Claims Status:{val_sum.get('status')}")
            print(f"Qualitative Scope:      {val_sum.get('qualitative_audit_status', 'UNVERIFIED_PENDING_HUMAN_AUDIT')}")
            print(f"Report Certification:   {val_sum.get('full_report_certification', 'PARTIAL_VERIFICATION_NUMERICAL_ONLY')}")
            print(f"Saved Commentary:       {res.get('commentary_path')}")
            print(f"Validation Report:      {res.get('validation_json_path')}")
        return 0
    except Exception as exc:
        print(f"\nExecution Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

