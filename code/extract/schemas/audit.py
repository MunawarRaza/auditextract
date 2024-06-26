from typing import Annotated
from pydantic import Field
from pydantic import BaseModel as PydanticBaseModel
from utils.audit_info_retrieval import AuditRetrieval

class BaseModel(PydanticBaseModel):
    """Change Pydantic config for all other classes"""

    class Config:
        # Removes warning: https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.protected_namespaces
        protected_namespaces = ("pydantic_model_",)
        
        
class AuditReportRequest(BaseModel):
    bucket_name: Annotated[str, Field(description="Name of the bucket where files are stored")]
    organization_id: Annotated[str, Field(description="The ID of the company associated with the `file_key`")]
    file_key: Annotated[str, Field(description="The File Key of the Report (S3 Object name)")]
    
class AuditInferenceResponse(BaseModel):
    user_id: Annotated[str, Field(description="User ID that requested the auditing")]
    file_key: Annotated[str, Field(description="File ID of the audited report")]
    audit_retrieval: Annotated[AuditRetrieval, Field(description="AI Information Retrieved (response)")]

class ReportData(BaseModel):
    file_key: Annotated[str, Field(description="File ID of the audited report")]
    report_data: Annotated[AuditRetrieval, Field(description="AI Information Retrieved (response)")]
    
class AuditRequest(BaseModel):
    original_report_name: Annotated[
        str,
        Field(
            description="The name of the original PDF report. This name will be used in the results file name"
        ),
    ]
    entities_bucket: Annotated[
        str, Field(description="The name of the bucket where to find the entities file")
    ]
    entities_path: Annotated[
        str, Field(description="The full path of the entities JSON file in the bucket")
    ]
    organization_id: Annotated[str, Field(description="The ID of the organization")]
