from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    croo_api_url: str = "https://api.croo.network"
    capscore_api_url: str = "http://localhost:8000"
    capscore_public_base_url: str = "http://localhost:8000"
    anthropic_api_key: str = ""
    max_job_seconds: int = 300
    max_repo_mb: int = 250
    allow_network_repro: bool = False
    log_level: str = "info"
    runs_dir: Path = Path("/app/runs")

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
