import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    YOUTUBE_CHANNEL_URL: str = os.getenv("YOUTUBE_CHANNEL_URL", "https://www.youtube.com/@NateBJones")
    
    PRIMARY_WINDOW_DAYS: int = 14
    OUTLIER_THRESHOLD_SD: float = 2.0
    REFRESH_CADENCE_HOURS: int = 24
    ARCHIVE_RETENTION_DAYS: int = 180
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    METADATA_DIR: str = os.path.join(DATA_DIR, "metadata")
    TRANSCRIPTS_DIR: str = os.path.join(DATA_DIR, "transcripts")

    @classmethod
    def validate(cls) -> dict:
        issues = []
        if not cls.ANTHROPIC_API_KEY:
            issues.append("ANTHROPIC_API_KEY missing")
        if not cls.DEEPGRAM_API_KEY:
            issues.append("DEEPGRAM_API_KEY missing")
        return {"valid": len(issues) == 0, "issues": issues}

config = Config()
