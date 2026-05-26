from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    HTTPException,
    Response,
    status,
)
from botocore.exceptions import ClientError
import boto3
import sys
import os

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()


KB = 1024
MB = 1024 * KB
MAX_EXPIRES = 7 * 24 * 3600

SUPPORTED_FILE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "application/pdf": "pdf",
}
AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
s3_client = boto3.client("s3", region_name=AWS_REGION)
ALLOWED_PREFIXES = ["Gestionale/"]


def _cap_expires(expires: int):
    return max(1, min(expires, MAX_EXPIRES))

def _is_allowed_key(key: str):
    return any(key.startswith(prefix) for prefix in ALLOWED_PREFIXES)

def normalize_legacy_key(key: str) -> str:
    if key.startswith("uploads/Gestionale/"):
        return key.removeprefix("uploads/")
    return key


#############################################
########## Generate PRE Signed URL ##########
########## Upload  ------ Download ##########
#############################################


@router.get("/presign-upload")
async def presign_upload(
    key: str,
    expires: int = 60,
    content_type: str | None = None,
    # current_user: dict = Depends(verify_cognito_token),
):
    """
    Generate a pre-signed URL for uploading a file (HTTP PUT) directly to S3.
    Example:
      GET /presign-upload?key=Gestionale/Fornitori/file.pdf&expires=60&content_type=application/pdf
    Client then PUTs the file bytes to the returned URL.
    """

    key = normalize_legacy_key(key)
    if not _is_allowed_key(key):
        raise HTTPException(status_code=400, detail="Key not allowed")

    params = {
        "Bucket": AWS_BUCKET,
        "Key": key,
    }
    # Encourage clients to send the same Content-Type they’ll use in the PUT request
    if content_type:
        params["ContentType"] = content_type

    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=_cap_expires(expires),
        )
        return {
            "url": url,
            "method": "PUT",
            "key": key,
            "expires_in": _cap_expires(expires),
            "headers": {"Content-Type": content_type} if content_type else {},
        }
    except ClientError as e:
        # logger.error(f"Presign upload failed for {key}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate pre-signed upload URL"
        )


@router.get("/presign-download")
async def presign_download(
    key: str,
    expires: int = 60,
    download_name: str | None = None,
    # current_user: dict = Depends(verify_cognito_token),
):
    """
    Generate a pre-signed URL for downloading a file (HTTP GET) from S3.
    Example:
      GET /presign-download?key=Gestionale/Emails/A.pdf&expires=60&download_name=Allegato.pdf
    """

    key = normalize_legacy_key(key)
    if not _is_allowed_key(key):
        raise HTTPException(status_code=400, detail="Key not allowed")

    params = {
        "Bucket": AWS_BUCKET,
        "Key": key,
    }
    if download_name:
        params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'

    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=_cap_expires(expires),
        )
        return {
            "url": url,
            "method": "GET",
            "key": key,
            "expires_in": _cap_expires(expires),
        }
    except ClientError as e:
        # logger.error(f"Presign download failed for {key}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate pre-signed download URL"
        )



@router.delete("/delete-file")
async def delete_file(
    key: str,
    # current_user: dict = Depends(verify_cognito_token),
):
    """
    Delete a file directly from S3 (no pre-signed URL needed)
    """

    key = normalize_legacy_key(key)
    if not _is_allowed_key(key):
        raise HTTPException(status_code=400, detail="Key not allowed")

    try:
        s3_client.delete_object(Bucket=AWS_BUCKET, Key=key)
        return {
            "success": True,
            "message": f"File {key} deleted successfully",
            "key": key,
        }
    except ClientError as e:
        # logger.error(f"Delete failed for {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


# --- end block ----------------------------------------------------------------
