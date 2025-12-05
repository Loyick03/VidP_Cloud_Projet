from pydantic import BaseModel
from typing import List, Optional

class VideoMetadata(BaseModel):
    video_id: str
    video_path: str
    subtitle_path: str
    language: str
    animals: List[str] = []
    duration_seconds: Optional[float] = None