from pydantic import BaseModel, Field


class BulkAnswerRequest(BaseModel):
    rfp_id: int = Field(gt=0)


class SingleAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
