from pydantic import BaseModel

class CoverLetterImproveRequest(BaseModel):
    instruction: str

class ImprovedCoverLetterResult(BaseModel):
    improved_text: str