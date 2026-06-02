from datetime import date
import os
import sys
import shutil
from fastapi import UploadFile
from pypdf import PdfReader
import re

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from routers.utils_parsing_models import *

############################################
########### DEFINER FUNCTIONS ##############
############################################

def tipologia_infissi_definer(text_line):

    if text_line in tipologia_infisso:
        return tipologia_infisso[text_line]
    else:
        return "None"

def soglia_infissi_definer(text_line):
    if text_line in soglia_infissi:
        return soglia_infissi[text_line]
    elif text_line[:1] in soglia_infissi:
        return soglia_infissi[text_line[:1]]
    else:
        return "None"

def nodo_centrale_definer(text_line):
    if text_line in nodo_centrale:
        return nodo_centrale[text_line]
    else:
        return "None"

def Modello_finestra__cerniere_codice_vetro_infissi_pattern_definer(text_line):
    if text_line in modello_finestra:
        return modello_finestra[text_line], 1
    elif text_line in cerniere:
        return cerniere[text_line], 2
    else:
        return "None", "None"

def colore_pvc_definer(text_line):
    if text_line in colore_pvc:
        return colore_pvc[text_line]
    else:
        return "None"

def modello_finestra_definer(text_line):
    if text_line in modello_finestra:
        return modello_finestra[text_line]
    else:
        return "None"

def cerniere_definer(text_line):
    # print('aa', text_line)
    if text_line[:1] in cerniere:
        # print('aaa', text_line[:1])
        # print('bbbb', cerniere[text_line[:1]])
        return cerniere[text_line[:1]]
    else:
        return "None"

def maniglie_infissi_definer(text_line):
    if text_line in maniglie_infissi:
        return maniglie_infissi[text_line]
    else:
        return "None"

def colore_maniglie_infissi_definer(text_line):
    if text_line in colore_maniglie_infissi:
        return colore_maniglie_infissi[text_line]
    else:
        return "None"

############################################
########### UTILS FUNCTIONS ################
############################################

def extract_numbers(string):
    # Use regex to find all sequences of digits in the string
    numbers = re.findall(r"\d+", string)

    # Convert the found sequences to integers
    numbers = [int(num) for num in numbers]

    return numbers[0]

def clean_design(raw: str) -> str:
    raw = raw.strip()

    # Remove page marker only: Page 1/6, Page 2/6, etc.
    raw = re.sub(r"Page\s+\d+/\d+", "", raw).strip()

    return raw

def get_quantity_and_design(lines, i):
    raw = lines[i - 1].strip() if i - 1 >= 0 else ""

    # Case: "Page 1/62 Infisso"
    # Means page marker "Page 1/6" + "2 Infisso"
    match = re.match(r"^Page\s+\d+/\d+(\d+)\s+(.+)$", raw)
    if match:
        qty = int(match.group(1))
        design = match.group(2).strip()
        return qty, design

    # Remove normal page marker
    raw = re.sub(r"Page\s+\d+/\d+", "", raw).strip()

    # Case: "3 Infisso"
    match = re.match(r"^(\d+)\s+(.+)$", raw)
    if match:
        qty = int(match.group(1))
        design = match.group(2).strip()
        return qty, design

    # Case: previous line is just number
    if i - 2 >= 0 and lines[i - 2].strip().isdigit():
        return int(lines[i - 2].strip()), raw

    return 1, raw

def pdf_to_text_from_upload(file: UploadFile) -> str:
    file.file.seek(0)
    reader = PdfReader(file.file)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text

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

def clean_and_enumerate(data):
    if data and isinstance(data[0], dict) and not data[0]:
        data = data[1:]  # Remove the first empty dictionary

    enumerated_data = {index + 1: obj for index, obj in enumerate(data)}
    return enumerated_data

def remove_trash(list2):
    res = {k: v for k, v in list2.items() if "ENOVA" not in v}

    return res

def delete_not_infisso(list2):
    for key in list(list2.keys()):
        if list2[key]["Design"].lower() != "infisso":
            del list2[key]

    return list2

def enumerate_properly(list1):
    new_dict = {i + 1: list1[key] for i, key in enumerate(list1)}

    return new_dict

def update_colore_pvc(list):

    # Update the 'Colore PVC' where necessary
    for key, infisso in list.items():
        if infisso.get('Colore PVC') == 'BIANCO LISCIO 01':
            infisso['Colore PVC'] = 'BIANCO EXTRALISCIO 01'

    return list

def append_object(all_obj, res, n_obj):
    if res:
        res["Quantita"] = int(n_obj) if str(n_obj).isdigit() else 1
        all_obj.append(res.copy())


############################################
########### FORNITORI PARSING ##############
############################################


def pdf_rules2(context2):
    lines = context2.split("\n")
    all_obj = []
    res = {}
    n_obj = 1
    flag_specifiche_condizioni = 0

    for i in range(len(lines)):
        line = lines[i].strip()

        if line == "":
            continue

        if line.startswith("●") and "(" in line:
            if "Fornitore" in line:
                append_object(all_obj, res, n_obj)

                res = {}
                n_obj, design = get_quantity_and_design(lines, i)

                res["Design"] = design
                res["Quantita"] = n_obj

            split_string = line.split("(", 1)
            key = split_string[0][1:].strip()
            value = split_string[1].replace(")", "").strip()

            res[key] = value

        if line in ["CONDIZIONI", "SPECIFICHE"] and flag_specifiche_condizioni == 0:
            flag_specifiche_condizioni = 1

            append_object(all_obj, res, n_obj)

            res = {}
            n_obj = 1

    append_object(all_obj, res, n_obj)

    return all_obj


############################################
########### CLIENTE PROJ PARSING ###########
############################################

def extract_cliente_info(text_content):
    lines = [line.strip() for line in text_content.split("\n")]

    cliente = {
        "nome": "",
        "citta": "",
        "indirizzo": "",
        "numero_tel": "",
        "email": "",
    }

    for i, line in enumerate(lines):

        if line == "COMMITTENTE" and i + 1 < len(lines):
            cliente["nome"] = lines[i + 1]

        elif line == "INDIRIZZO" and i + 1 < len(lines):
            cliente["indirizzo"] = lines[i + 1]

        elif line == "CITTÀ" and i + 1 < len(lines):
            cliente["citta"] = lines[i + 1]

        elif line == "CELLULARE" and i + 1 < len(lines):
            value = lines[i + 1]
            if value and value[0].isdigit():
                cliente["numero_tel"] = value

        elif line == "EMAIL" and i + 1 < len(lines):
            value = lines[i + 1]
            if "@" in value:
                cliente["email"] = value

        # stop when products start
        if re.match(r"^\d+\s+Infisso$", line):
            break

    return {"Cliente": cliente}

def extract_progetto_info(text_content):
    lines = [line.strip() for line in text_content.split("\n")]

    progetto = {
        "azienda": lines[0] if len(lines) > 0 else "",
        "centro_di_costo": lines[1] if len(lines) > 1 else "",
        "commerciale": "",
        "importo": "",
        "data_primo_pagamento": date.today().isoformat(),
    }

    for i, line in enumerate(lines):

        if line == "ADDETTO" and i + 1 < len(lines):
            progetto["commerciale"] = lines[i + 1]

        elif "IMPONIBILE" in line and i + 1 < len(lines):
            progetto["importo"] = lines[i + 1]

    return {"Progetto": progetto}

def build_fornitori_dict(list2):
    fornitori = {}

    for item in list2:
        fornitore = item.get("Fornitore")
        prodotto = item.get("Design")
        quantita = item.get("Quantita", 1)

        if not fornitore or not prodotto:
            continue

        if fornitore not in fornitori:
            fornitori[fornitore] = {
                "prodotti": []
            }

        fornitori[fornitore]["prodotti"].append({
            "prodotto": prodotto,
            "quantita": str(quantita)
        })

    return {
        "fornitori": fornitori
    }
