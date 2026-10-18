"""HTTP input contracts; no changes to native Repair schemas or prompts."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WebError(ValueError):
    def __init__(self, code: str, status: int = 422):
        self.code, self.status = code, status
        super().__init__(code)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Selection(StrictModel):
    step_id: int = Field(gt=0, strict=True)
    global_id: str | None = Field(default=None, max_length=128)
    view_version: str = Field(min_length=1, max_length=128)


class PrepareRequest(StrictModel):
    input_id: str = Field(pattern=r'^input-[a-f0-9]{32}$')
    user_text: str = Field(min_length=1, max_length=16384)
    language: Literal['zh', 'en'] = 'zh'
    view_version: str | None = Field(default=None, max_length=128)
    primary: Selection | None = None
    auxiliary: Selection | None = None
    targets: list[Selection] | None = Field(default=None, max_length=16)

    @model_validator(mode='after')
    def distinct_input_forms(self):
        if self.targets is not None and self.primary is not None:
            raise ValueError('USE_TARGETS_OR_PRIMARY_NOT_BOTH')
        return self

    @field_validator('user_text')
    @classmethod
    def validate_text(cls, value):
        if not value.strip() or len(value.encode('utf-8')) > 16384:
            raise ValueError('REQUEST_TEXT_EMPTY_OR_TOO_LARGE')
        return value  # Do not trim or rewrite the user's words.


class StartRequest(StrictModel):
    prepared_request_id: str = Field(pattern=r'^request-[a-f0-9]{32}$')
    client_request_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9._:-]+$')


class AnswerRequest(StrictModel):
    clarification_id: str = Field(min_length=1, max_length=128)
    expected_state_version: int = Field(ge=0, strict=True)
    client_answer_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9._:-]+$')
    answer: dict[str, Any]
