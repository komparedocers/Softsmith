"""
LLM Router - Unified interface for multiple LLM providers.
Supports OpenAI, Claude, and local LLM APIs with configurable routing.
"""
import os
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
import openai
from anthropic import AsyncAnthropic
import httpx
from .config import get_config, get_settings
from .logging import get_logger

logger = get_logger(__name__)


class LLMRole(str, Enum):
    """Predefined roles for LLM routing."""
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"


class LLMRouter:
    """Routes LLM requests to appropriate providers."""

    def __init__(self):
        self.config = get_config()
        self.settings = get_settings()
        self._clients: Dict[str, Any] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize LLM client instances."""
        llm_config = self.config.llm

        # OpenAI
        if llm_config.providers.get("openai", {}).enabled:
            api_key = getattr(self.settings, llm_config.providers["openai"].api_key_env.lower(), None)
            if api_key:
                self._clients["openai"] = openai.AsyncOpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client")

        # Claude/Anthropic
        if llm_config.providers.get("claude", {}).enabled:
            api_key = getattr(self.settings, llm_config.providers["claude"].api_key_env.lower(), None)
            if api_key:
                self._clients["claude"] = AsyncAnthropic(api_key=api_key)
                logger.info("Initialized Claude client")

        # Local LLM
        if llm_config.providers.get("local", {}).enabled:
            base_url = llm_config.providers["local"].base_url
            self._clients["local"] = httpx.AsyncClient(base_url=base_url)
            logger.info("Initialized local LLM client", base_url=base_url)

    def _get_providers_for_role(self, role: str) -> List[str]:
        """Get list of providers for a specific role."""
        routing = self.config.llm.routing
        providers = routing.get(role, [])

        # Fallback to first enabled provider if role not configured
        if not providers:
            for provider_name, provider_config in self.config.llm.providers.items():
                if provider_config.enabled:
                    providers = [provider_name]
                    break

        # Filter to only enabled providers
        enabled_providers = []
        for p in providers:
            if self.config.llm.providers.get(p, {}).enabled:
                enabled_providers.append(p)

        return enabled_providers

    async def _call_openai(
        self,
        provider_config: Any,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Call OpenAI API."""
        client = self._clients.get("openai")
        if not client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = await client.chat.completions.create(
                model=provider_config.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", provider_config.max_tokens),
                temperature=kwargs.get("temperature", provider_config.temperature),
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise

    async def _call_claude(
        self,
        provider_config: Any,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Call Claude API."""
        client = self._clients.get("claude")
        if not client:
            raise ValueError("Claude client not initialized")

        try:
            # Convert messages format for Claude
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
            user_messages = [m for m in messages if m["role"] != "system"]

            response = await client.messages.create(
                model=provider_config.model,
                max_tokens=kwargs.get("max_tokens", provider_config.max_tokens),
                temperature=kwargs.get("temperature", provider_config.temperature),
                system=system_msg,
                messages=user_messages,
            )
            return response.content[0].text

        except Exception as e:
            logger.error("Claude API call failed", error=str(e))
            raise

    async def _call_local(
        self,
        provider_config: Any,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Call local LLM API (OpenAI-compatible)."""
        client = self._clients.get("local")
        if not client:
            raise ValueError("Local LLM client not initialized")

        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": provider_config.model,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", provider_config.max_tokens),
                    "temperature": kwargs.get("temperature", provider_config.temperature),
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error("Local LLM API call failed", error=str(e))
            raise

    async def call_llm(
        self,
        role: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Call LLM with automatic provider routing based on role.

        Args:
            role: The role/purpose of this LLM call (planning, code_generation, etc.)
            prompt: The user prompt/question
            context: Additional context dictionary
            system_message: Optional system message
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            The LLM response text
        """
        providers = self._get_providers_for_role(role)

        if not providers:
            raise ValueError(f"No enabled providers found for role: {role}")

        logger.info(
            "Routing LLM call",
            role=role,
            providers=providers,
            prompt_length=len(prompt)
        )

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append({"role": "system", "content": f"Context:\n{context_str}"})

        messages.append({"role": "user", "content": prompt})

        # Try providers in order with fallback
        last_error = None
        for provider_name in providers:
            try:
                provider_config = self.config.llm.providers[provider_name]

                if provider_name == "openai":
                    result = await self._call_openai(provider_config, messages, **kwargs)
                elif provider_name == "claude":
                    result = await self._call_claude(provider_config, messages, **kwargs)
                elif provider_name == "local":
                    result = await self._call_local(provider_config, messages, **kwargs)
                else:
                    logger.warning(f"Unknown provider: {provider_name}")
                    continue

                logger.info(
                    "LLM call successful",
                    role=role,
                    provider=provider_name,
                    response_length=len(result)
                )
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM provider failed, trying next",
                    provider=provider_name,
                    error=str(e)
                )

                if not self.config.llm.fallback_enabled:
                    raise

        # All providers failed
        raise Exception(f"All LLM providers failed for role {role}. Last error: {last_error}")

    async def call_multiple(
        self,
        role: str,
        prompt: str,
        providers: List[str],
        **kwargs
    ) -> Dict[str, str]:
        """
        Call multiple providers in parallel and return all results.
        Useful for ensembling or comparison.
        """
        tasks = []
        for provider in providers:
            if self.config.llm.providers.get(provider, {}).enabled:
                tasks.append(self.call_llm(role, prompt, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            provider: result if not isinstance(result, Exception) else str(result)
            for provider, result in zip(providers, results)
        }


# Global router instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
