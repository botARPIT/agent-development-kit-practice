from pydantic import BaseModel, Field

class OutlineSchema(BaseModel):
    title: str = Field(
        json_schema_extra="Catchy headline for the blog"
        ),

    introduction_hook: str = Field(
        json_schema_extra="Introduction hook for the blog. Should be concise and clear"
    )

    main_section: str = Field(
        json_scheme_extra = "Contains the main body of the blog"
    )

    conclusion: str = Field(
        json_schema_extra= "Conclusion thought for the blog"
    )

    additional_innformation: str = Field(
        json_schema_extra="Additional information required by other agents"
    )