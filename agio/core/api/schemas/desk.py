from uuid import UUID
from pydantic import BaseModel, EmailStr, HttpUrl

# profile

class ProfileLanguage(BaseModel):
    code: str
    name: str
    nativeName: str


class ProfileGroup(BaseModel):
    id: UUID
    name: str


class UserProfileResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    firstName: str
    lastName: str
    avatar: HttpUrl
    language: ProfileLanguage
    groups: list[ProfileGroup]


# company

class CompanyResponseSchema(BaseModel):
    id: UUID
    name: str
    code: str
    legalName: str
    email: str | None
    logo: HttpUrl | None


class CurrentCompanyResponseSchema(CompanyResponseSchema):
    pass
