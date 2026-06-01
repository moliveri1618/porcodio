import os
import shutil
from fastapi import UploadFile


def save_pdf(file: UploadFile, folder_name: str) -> str:
    # Directory where this file is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Folder that will contain the PDF
    files_dir = os.path.join(script_dir, folder_name)

    # Delete old folder and contents
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir)

    # Create empty folder
    os.makedirs(files_dir)

    # Full path of uploaded PDF
    file_path = os.path.join(files_dir, file.filename)

    # Save PDF
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path
