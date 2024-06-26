import os
import sys
import boto3
import logging
import requests
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from functools import lru_cache
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.audit_info_retrieval import AuditRetrieval
from utils.report_s3_utils import get_report_from_s3, upload_report_to_s3
from utils.get_keywords import get_keywords_table
from utils.report_content_processing import ReportProcessor
from utils.report_entity_extraction import ReportEntityExtraction
from extract.schemas.audit import (
    AuditReportRequest,
    AuditRequest,
)
import spacy

@lru_cache
def get_environment() -> str:
    environment = os.environ.get("ENVIRONMENT", None)
    if environment is None:
        print("WARNING: 'ENVIRONMENT' env var is not set, using 'quality' as default.")
        environment = "quality"
    return environment

logging.info("Connecting to DynamoDB...")
KEYWORDS_TABLE_NAME = "luminous_audit_keywords"
# S3_BUCKET_AUDIT = f"{get_environment()}-luminous-audit-files"
S3_BUCKET_AUDIT = "quality-luminous-audit-extract"
REGION_NAME = "us-east-2"
dynamodb: DynamoDBServiceResource = boto3.resource(
    "dynamodb",
    region_name=REGION_NAME,
)

# Initialize app
app = FastAPI(
    title="Luminous Audit - Endpoints",
    description="Endpoints to retrieve information from a report",
    version="0.1.1"
)

# AUDIT_BUCKET_NAME = "quality-luminous-audit"
REGION_NAME = "us-east-2"

# Load Spacy Model:
nlp = spacy.load("en_core_web_sm")

# Redirect /docs#
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Information retrieval endpoint
@app.post("/audit/info_retrieval")
async def info_retrieval(body: AuditReportRequest): 
    """Asks the AI to generate a new message for the current conversation."""
    # Get Report data (Textract extraction)
    try:
        report_object_dict = get_report_from_s3(body)
    except KeyError:
        raise HTTPException(status_code=404, detail="file_key not found")

    # Process Page Data
    report_processor = ReportProcessor(original_content=report_object_dict["data"])
    processed_data = report_processor.process_content()
    
    keywords_data = get_keywords_table(
        dynamodb=dynamodb,
        table_name=KEYWORDS_TABLE_NAME
    )
    
    print(f"Extracting entities: {body.file_key}")
    start_time = time.time()
    entity_extractor = ReportEntityExtraction(
        data=processed_data, 
        nlp_model=nlp, 
        keywords_dict=keywords_data,
        report_name = body.file_key.replace('.json','')
    )
    entities_result: AuditRetrieval = entity_extractor.transform_data()
    print(f"Entity extraction complete --- {round((time.time() - start_time),2)} seconds ---")
    
    # print(json_output)
    print(f"Uploading entities extraction to S3: {body.file_key}")
    start_time = time.time()
    object_name = f"organization/{body.organization_id}/{body.file_key.replace('.json','_entities.json')}"
    s3_upload = upload_report_to_s3(
        data = entities_result, 
        metadata = report_object_dict["metadata"],
        bucket_name=S3_BUCKET_AUDIT, 
        object_name=object_name
        )
    print(f"Entities file uploaded to S3 --- {round((time.time() - start_time),2)} seconds ---")

    # Trigger Audit-rules:
    if s3_upload:
        # print("Trigger Audit Rules")
        response = AuditRequest( 
            original_report_name = body.file_key.replace('.json',''),
            entities_bucket = body.bucket_name,
            entities_path = object_name,
            organization_id = body.organization_id
        ).model_dump()
        
    #     # Call audit-rules
    #     audit_rules_callback_response = requests.post(
    #         url=f"https://{get_environment()}-audit-rules.gasai.us/audit",
    #         json=response,
    #     )
    #     if audit_rules_callback_response.status_code not in range(200, 300):
    #         be_response_error = (
    #             "ERROR: BE did not respond as expected, audit results might have not been received."
    #             f" Tried to send: {response}; and received: {audit_rules_callback_response}"
    #         )
    #         print(be_response_error)
    #         raise HTTPException(status_code=500, detail=be_response_error)

    return {
        "message": "Audit Extraction completed, response for audit rules is ready.",
        "response": response,
    }

if __name__ == "__main__":
    from pathlib import Path as PPath
    import uvicorn
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    # python3 -m code.ai.inference.audit_inference
    
    uvicorn.run(f"{PPath(__file__).stem}:app", host="127.0.0.1", port=5555, reload=True)