"""Anthropic client helpers for Azure-hosted Claude."""

from __future__ import annotations

import os
from typing import Optional

from anthropic import AsyncAnthropic


def create_azure_anthropic_client(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> AsyncAnthropic:
    """
    Create an Anthropic client configured for Azure.

    Args:
        api_key: Azure API key (defaults to AZURE_KEY env var)
        endpoint: Azure endpoint URL (defaults to AZURE_ENDPOINT env var)

    Returns:
        AsyncAnthropic client configured for Azure
    """
    api_key = api_key or os.environ.get("AZURE_KEY")
    endpoint = endpoint or os.environ.get("AZURE_ENDPOINT")

    if not api_key:
        raise ValueError("API key required - set AZURE_KEY env var or pass api_key")
    if not endpoint:
        raise ValueError("Endpoint required - set AZURE_ENDPOINT env var or pass endpoint")

    # Azure Anthropic endpoint should end with /anthropic
    base_url = endpoint.rstrip("/")
    if not base_url.endswith("/anthropic"):
        base_url = f"{base_url}/anthropic"

    return AsyncAnthropic(
        api_key=api_key,
        base_url=base_url,
    )
