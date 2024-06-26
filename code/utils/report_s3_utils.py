import boto3
import json
from botocore.exceptions import (
    NoCredentialsError, 
    PartialCredentialsError, 
    ClientError
)
from pydantic import BaseModel

class FileRequest(BaseModel):
    bucket_name: str
    organization_id: str
    file_key: str
    
def get_report_from_s3(file_request: FileRequest):
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name='us-east-2')

    try:
        # Construct the S3 object key
        object_key = f"organization/{file_request.organization_id}/{file_request.file_key}"

        # Get the object from S3
        response = s3_client.get_object(Bucket=file_request.bucket_name, Key=object_key)
        json_content = response['Body'].read().decode('utf-8')
        metadata = response['Metadata']

        return {
            "data": json_content,
            "metadata": metadata
        }
        
    except NoCredentialsError:
        raise NoCredentialsError("Credentials not available")
    except PartialCredentialsError:
        raise PartialCredentialsError("Incomplete credentials")
    except Exception as e:
        raise Exception(str(e))
 

def upload_report_to_s3(data: dict, metadata: dict, bucket_name: str, object_name: str) -> bool:
    """Uploads a entity results as a JSON file to an Amazon S3 bucket.

    Args:
        data (dict): The dictionary to upload.
        bucket_name (str): The name of the S3 bucket.
        object_name (str): The object name under which the JSON file is saved in the bucket.

    Returns:
        bool: True if file was uploaded, else False.
    """

    # Initialize the S3 client
    s3_client = boto3.client("s3", region_name="us-east-1")
    
    # Convert the dictionary into a JSON string
    json_string = json.dumps(data)

    try:
        # Upload the JSON string to S3
        s3_client.put_object(
            Body=json_string, 
            Bucket=bucket_name, 
            Key=object_name,
            Metadata=metadata if metadata else {}
            )
        print(f"File uploaded successfully to {bucket_name}/{object_name}")
        return True
    except NoCredentialsError:
        raise NoCredentialsError("Failed to upload the file: Credentials not available")
    except PartialCredentialsError:
        raise PartialCredentialsError("Failed to upload the file: Incomplete credentials")
    except ClientError:
        raise ClientError("Failed to upload the file: ClientError")
    except Exception as e:
        raise Exception(str(e))
       
# Usage Example
if __name__ == "__main__":
    
    from pydantic import BaseModel
     
    class AuditReportRequest(BaseModel):
        bucket_name: str
        organization_id: str
        file_key: str
        
    request = AuditReportRequest(
        bucket_name='quality-luminous-audit-files',
        organization_id='1',
        file_key='Eagle Chief Midstream, LLC Carmen 1.2 JJJJ 6-14-16.pdf.json'
    )
    obj = get_report_from_s3(request)
