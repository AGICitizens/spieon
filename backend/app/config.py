from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _running_in_container() -> bool:
    return Path("/.dockerenv").exists()


def _replace_hostname(
    url: str,
    current_host: str,
    next_host: str,
    next_port: int | None = None,
) -> str:
    parts = urlsplit(url)
    if parts.hostname != current_host:
        return url

    userinfo = ""
    if parts.username is not None:
        userinfo = quote(parts.username, safe="")
        if parts.password is not None:
            userinfo += f":{quote(parts.password, safe='')}"
        userinfo += "@"

    host = next_host
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = parts.port if next_port is None else next_port
    if port is not None:
        host = f"{host}:{port}"

    return urlunsplit(
        (
            parts.scheme,
            f"{userinfo}{host}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
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

    # LLM — OpenRouter (OpenAI-compatible)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    judge_model: str = "anthropic/claude-3.5-haiku"

    # LLM — 0G Compute Network (OpenAI-compatible router). When `zerog_compute_api_key`
    # is set, the agent prefers 0G Compute over OpenRouter for planner/reflector/judge.
    zerog_compute_api_key: str = ""
    zerog_compute_base_url: str = "https://router-api.0g.ai/v1"
    zerog_compute_model: str = ""
    zerog_compute_judge_model: str = ""

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

    # KeeperHub — paid-per-execution workflow runner. The agent uses x402 to pay each
    # execute call (KeeperHub is x402-native). API key is used for management (create
    # workflow, list executions). When `keeperhub_payout_workflow_id` is unset, the
    # backend skips KH and only does the direct on-chain payout.
    keeperhub_api_key: str = ""
    keeperhub_base_url: str = "https://app.keeperhub.com/api"
    keeperhub_payout_workflow_id: str = ""

    # Operator (dev)
    operator_test_address: str = ""

    # ENS — agent identity. `ens_name` is the name the agent owns (e.g. spieon-agent.eth
    # on Sepolia). `ens_rpc_url` is the chain ENS resolves on; default Sepolia public RPC.
    # When `ens_name` is empty, the descriptor and stats endpoints omit ENS fields.
    ens_name: str = ""
    ens_rpc_url: str = "https://ethereum-sepolia-rpc.publicnode.com"
    ens_chain_id: int = 11155111
    ens_text_keys: str = "url,description,com.github,org.erc8004.descriptor,org.spieon.scan-endpoint,avatar"

    # Storage
    zerog_endpoint: str = ""
    zerog_api_key: str = ""
    ipfs_pinning_endpoint: str = ""
    ipfs_pinning_token: str = ""
    bundle_local_dir: str = "/tmp/spieon-bundles"

    @model_validator(mode="after")
    def normalize_local_service_hosts(self) -> "Settings":
        if _running_in_container():
            return self

        self.database_url = _replace_hostname(self.database_url, "postgres", "localhost")
        self.database_url_sync = _replace_hostname(
            self.database_url_sync,
            "postgres",
            "localhost",
        )
        self.langfuse_host = _replace_hostname(
            self.langfuse_host,
            "langfuse",
            "localhost",
            3001,
        )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
