from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ollama_host: str = "http://127.0.0.1:11434"
    model_name: str = "qwen3-coder-next"
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    api_token: str = ""
    max_context_tokens: int = 8192
    max_agent_steps: int = 30
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 1024
    request_timeout: float = 300.0
    auto_approve_safe_tools: bool = True
    auto_approve_medium_tools: bool = False
    auto_approve_high_tools: bool = False
    auto_approve_critical_tools: bool = False
    volt_workspace: Path = Path(".")
    database_path: Path = Path("data/memory.db")
    skills_path: Path = Path("skills")
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False, extra="ignore")

    def workspace(self) -> Path:
        return self.volt_workspace.expanduser().resolve()
