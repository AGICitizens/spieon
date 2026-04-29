from __future__ import annotations

from dataclasses import dataclass

from e2b_code_interpreter import AsyncSandbox

from app.config import get_settings


@dataclass(slots=True)
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    error: str | None = None


def is_configured() -> bool:
    return bool(get_settings().e2b_api_key)


async def run_in_sandbox(
    command: str,
    *,
    timeout: int = 60,
    envs: dict[str, str] | None = None,
) -> SandboxResult:
    if not is_configured():
        raise RuntimeError("E2B_API_KEY is not set")

    settings = get_settings()
    sandbox = await AsyncSandbox.create(
        timeout=timeout,
        envs=envs,
        api_key=settings.e2b_api_key,
    )
    try:
        execution = await sandbox.commands.run(command, timeout=timeout)
        return SandboxResult(
            stdout=execution.stdout or "",
            stderr=execution.stderr or "",
            exit_code=execution.exit_code or 0,
            error=getattr(execution, "error", None),
        )
    finally:
        try:
            await sandbox.kill()
        except Exception:
            pass
