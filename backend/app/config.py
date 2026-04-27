from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Runtime
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str
    database_url_sync: str

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "claude-opus-4-7"
    judge_model: str = "claude-haiku-4-5-20251001"

    # Langfuse
    langfuse_host: str = "http://langfuse:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # e2b
    e2b_api_key: str = ""

    # Chain — Base Sepolia
    base_sepolia_rpc_url: str = "https://sepolia.base.org"
    base_sepolia_chain_id: int = 84532
    agent_private_key: str = ""
    agent_address: str = ""
    cold_safe_address: str = ""

    # EAS
    eas_contract_address: str = "0x4200000000000000000000000000000000000021"
    eas_schema_registry_address: str = "0x4200000000000000000000000000000000000020"
    eas_schema_uid: str = ""

    # Spieon contracts (filled post-deploy)
    module_registry_address: str = ""
    bounty_pool_address: str = ""
    bounty_payout_module_address: str = ""

    # x402
    x402_facilitator_url: str = "https://x402.org/facilitator"
    x402_usdc_address: str = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

    # Operator (dev)
    operator_test_address: str = ""

    # Storage
    zerog_endpoint: str = ""
    zerog_api_key: str = ""
    ipfs_pinning_endpoint: str = ""
    ipfs_pinning_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
