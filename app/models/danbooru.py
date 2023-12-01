from typing import Optional

from pydantic import BaseModel, ConfigDict


class DanbooruPost(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    large_file_url: str
    file_ext: str
    rating: Optional[str]
    tag_string: Optional[str]
    tag_string_artist: Optional[str]
    tag_string_character: Optional[str]
