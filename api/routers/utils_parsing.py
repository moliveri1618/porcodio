import os
import shutil
from fastapi import UploadFile
from pypdf import PdfReader


def pdf_to_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    text_content = ""

    for page in reader.pages:
        text_content += page.extract_text() or ""

    return text_content


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


def define_txtfile_path(pdf_path: str, txt_file_name: str) -> str:
    pdf_dir = os.path.dirname(pdf_path)
    txt_path = os.path.join(pdf_dir, txt_file_name)

    return txt_path
