"""Central configuration loaded from environment / .env.

All external integrations degrade gracefully to mock mode when their keys are
absent, so the whole system runs end-to-end without any secrets.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Threads
    threads_access_token: str = ""
    threads_user_id: str = ""

    # Rakuten
    rakuten_application_id: str = ""
    rakuten_affiliate_id: str = ""
    rakuten_access_key: str = ""

    # A8
    a8_login_id: str = ""
    a8_enabled: bool = False

    # DB
    database_url: str = "sqlite:///./data/threads_ai.db"

    # Safety / behavior
    auto_publish: bool = False
    target_posts_per_day: int = 10
    affiliate_posts_per_day: int = 4
    value_posts_per_day: int = 3
    conversation_posts_per_day: int = 2
    experiment_posts_per_day: int = 1
    max_affiliate_posts_per_day: int = 4

    min_post_interval_minutes: int = 60
    min_affiliate_score: int = 70
    min_compliance_score: int = 90
    copy_similarity_threshold: float = 0.80
    min_exploration_ratio: float = 0.20

    # Posting window (posts are staggered between these hours, local time)
    first_post_hour: int = 8
    last_post_hour: int = 22

    # When the app starts, auto-generate today's candidates if none exist yet
    # (so a double-click gives you candidates ready to approve).
    generate_on_startup: bool = True

    # Browser
    browser_enabled: bool = False
    browser_headless: bool = True

    # Scheduler
    cron_daily_research: str = "06:00"
    cron_keyword_discovery: str = "06:30"
    cron_product_matching: str = "06:45"
    cron_content_generation: str = "07:00"  # candidates ready before 08:00 posting
    cron_daily_analysis: str = "23:00"
    cron_strategy_update: str = "00:00"

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000
    # Optional Basic-Auth lock for public deployments. When password is set,
    # every page except /healthz requires this user/password.
    dashboard_user: str = "admin"
    dashboard_password: str = ""

    # --- Derived / capability flags ---
    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def rakuten_enabled(self) -> bool:
        return bool(self.rakuten_application_id)

    @property
    def threads_publish_enabled(self) -> bool:
        return bool(self.threads_access_token and self.threads_user_id)

    @property
    def seed_keywords(self) -> List[str]:
        return [
            "便利グッズ", "旅行", "海外旅行", "国内旅行", "収納", "家電", "美容",
            "ヘアケア", "スキンケア", "キッチン", "料理", "掃除", "洗濯", "育児",
            "子育て", "デスク", "仕事効率化", "睡眠", "ファッション", "食品",
            "ギフト", "アウトドア", "キャンプ", "車", "ペット", "防災",
            "新生活", "ふるさと納税", "節約", "時短",
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
