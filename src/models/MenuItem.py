import sys
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class MenuItem(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True
    )

    id: str = Field(..., min_length=2)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    is_available: bool = Field(default=True)
    description: Optional[str] = Field(default="")
    prep_time: Optional[int] = Field(default=0, ge=0)
