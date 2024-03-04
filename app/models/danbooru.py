from typing import Optional

from pydantic import BaseModel, ConfigDict


class DanbooruPost(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    large_file_url: Optional[str] = None
    file_ext: str
    file_size: Optional[int]
    preview_file_url: Optional[str] = None
    rating: Optional[str]
    tag_string: Optional[str]
    tag_string_artist: Optional[str]
    tag_string_character: Optional[str]
    tag_string_copyright: Optional[str]
