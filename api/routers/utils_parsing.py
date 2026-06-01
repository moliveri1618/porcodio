import os
import shutil
from fastapi import UploadFile
import fitz  # PyMuPDF


def pdf_to_text(pdf_path: str, txt_path: str) -> None:
    pdf_document = fitz.open(pdf_path)

    text_content = ""

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text_content += page.get_text()

    with open(txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(text_content)

    pdf_document.close()


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
