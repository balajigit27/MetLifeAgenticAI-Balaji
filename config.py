"""
Configuration module for LLM initialization and environment setup.

This module provides:
- Unified LLM factory (supports both OpenAI and local Ollama)
- Environment configuration loading
- Validation of required settings
- Seamless cloud/local switching

Usage:
    from config import get_llm, settings
    
    llm = get_llm()  # Uses LLM_MODE from environment
    print(f"Using LLM: {settings.llm_mode}")
"""

import os
from typing import Literal
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Mode
    llm_mode: Literal["cloud", "local"] = "cloud"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 4096

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_temperature: float = 0.3
    ollama_max_tokens: int = 4096

    # Logging & Persistence
    log_level: str = "INFO"
    reports_dir: str = "./reports"
    db_path: str = "./research.db"

    # LangSmith (Optional)
    langsmith_enabled: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "agentic-research"

    # Research Parameters
    default_research_depth: Literal["quick", "standard", "deep"] = "standard"
    max_search_results: int = 5
    request_timeout: int = 30
    max_retries: int = 3

    # Feature Flags
    enable_checkpoints: bool = True
    json_logging: bool = False
    debug_mode: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def validate_llm_config(self) -> None:
        """Validate that required LLM configuration is present."""
        if self.llm_mode == "cloud":
            if not self.openai_api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY in .env or environment."
                )
        elif self.llm_mode == "local":
            # Ollama doesn't require an API key, but we'll verify URL is accessible
            pass


# Global settings instance
settings = Settings()


def validate_settings() -> None:
    """Validate settings on application startup."""
    settings.validate_llm_config()
    
    # Create required directories
    os.makedirs(settings.reports_dir, exist_ok=True)
    
    # Verify LangSmith configuration if enabled
    if settings.langsmith_enabled and not settings.langsmith_api_key:
        print("⚠️  LangSmith enabled but API key not set. Disabling LangSmith.")
        settings.langsmith_enabled = False


@lru_cache(maxsize=1)
def get_llm(mode: Literal["cloud", "local"] | None = None):
    """
    Get LLM instance based on configuration.
    
    Args:
        mode: Override default LLM mode. If None, uses settings.llm_mode
        
    Returns:
        LangChain LLM instance (ChatOpenAI or ChatOllama)
        
    Raises:
        ValueError: If configuration is invalid
        
    Example:
        llm = get_llm()  # Uses environment setting
        response = llm.invoke("What is AI?")
        
        # Override for a single call
        local_llm = get_llm(mode="local")
        response = local_llm.invoke("Quick question")
    """
    mode = mode or settings.llm_mode
    
    if mode == "cloud":
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            request_timeout=settings.request_timeout,
        )
    elif mode == "local":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature,
            num_predict=settings.ollama_max_tokens,
            request_timeout=settings.request_timeout,
        )
    else:
        raise ValueError(f"Invalid LLM mode: {mode}. Must be 'cloud' or 'local'")


def get_llm_info() -> dict:
    """
    Get current LLM configuration info (for debugging).
    
    Returns:
        Dictionary with LLM configuration
    """
    if settings.llm_mode == "cloud":
        return {
            "mode": "cloud",
            "provider": "OpenAI",
            "model": settings.openai_model,
            "temperature": settings.openai_temperature,
            "max_tokens": settings.openai_max_tokens,
        }
    else:
        return {
            "mode": "local",
            "provider": "Ollama",
            "url": settings.ollama_base_url,
            "model": settings.ollama_model,
            "temperature": settings.ollama_temperature,
            "max_tokens": settings.ollama_max_tokens,
        }


if __name__ == "__main__":
    # Quick test on import
    print("✓ Configuration module loaded successfully")
    print(f"  LLM Mode: {settings.llm_mode}")
    print(f"  LLM Info: {get_llm_info()}")
