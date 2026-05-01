"""
Settings endpoint — read and update LLM configuration at runtime.
Updates take effect immediately by re-initializing microcore.
"""

import os
import logging

import microcore as mc
from fastapi import APIRouter, HTTPException

from backend.schemas import LLMSettingsResponse, LLMSettingsUpdate

router = APIRouter()
logger = logging.getLogger(__name__)

# Supported provider presets shown in the UI dropdown
SUPPORTED_PROVIDERS = [
    {"value": "google", "label": "Google Gemini", "placeholder": "AIza..."},
    {"value": "openai", "label": "OpenAI", "placeholder": "sk-..."},
    {"value": "anthropic", "label": "Anthropic Claude", "placeholder": "sk-ant-..."},
]


@router.get("/", response_model=LLMSettingsResponse)
async def get_settings():
    """Return the current LLM configuration (never exposes the raw API key)."""
    cfg = mc.config()
    return LLMSettingsResponse(
        llm_api_type=str(cfg.LLM_API_TYPE or ""),
        model=str(cfg.MODEL or ""),
        has_api_key=bool(cfg.LLM_API_KEY),
        embedding_model=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        vector_store_path=os.environ.get("VECTOR_STORE_PATH", ""),
    )


@router.get("/providers")
async def list_providers():
    """Return the list of supported LLM providers for the UI dropdown."""
    return SUPPORTED_PROVIDERS


@router.put("/", response_model=LLMSettingsResponse)
async def update_settings(update: LLMSettingsUpdate):
    """
    Update LLM settings at runtime.
    Re-initializes microcore so changes take effect immediately.
    """
    # Build kwargs — only override what was provided
    env_overrides: dict = {}

    if update.llm_api_key is not None:
        os.environ["LLM_API_KEY"] = update.llm_api_key
        env_overrides["LLM_API_KEY"] = update.llm_api_key

    if update.llm_api_type is not None:
        os.environ["LLM_API_TYPE"] = update.llm_api_type
        env_overrides["LLM_API_TYPE"] = update.llm_api_type

    if update.model is not None:
        os.environ["MODEL"] = update.model
        env_overrides["MODEL"] = update.model

    # Re-initialize microcore with updated env vars
    try:
        from pathlib import Path

        gito_tpl_path = Path(__file__).resolve().parent.parent.parent.parent / "gito" / "tpl"

        mc.configure(
            USE_LOGGING=True,
            VALIDATE_CONFIG=False,
            EMBEDDING_DB_TYPE=mc.EmbeddingDbType.NONE,
            PROMPT_TEMPLATES_PATH=[".gito", str(gito_tpl_path)],
        )

        cfg = mc.config()
        logger.info(
            f"microcore reconfigured: api_type={cfg.LLM_API_TYPE}, "
            f"model={cfg.MODEL}, platform={cfg.LLM_API_PLATFORM}"
        )

        return LLMSettingsResponse(
            llm_api_type=str(cfg.LLM_API_TYPE or ""),
            model=str(cfg.MODEL or ""),
            has_api_key=bool(cfg.LLM_API_KEY),
            embedding_model=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            vector_store_path=os.environ.get("VECTOR_STORE_PATH", ""),
        )

    except Exception as e:
        logger.error(f"Failed to reconfigure LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply settings: {e}")
