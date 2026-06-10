from datetime import date
import os
import sys
import shutil
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
import re
from sqlmodel import Session, select
from sqlalchemy import func
import unicodedata
import re

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from routers.utils_parsing_models import *
from models.clienti import Cliente
from models.fornitori import Fornitore
from models.scheda_tecnica_schema import SchedaTecnicaSchema
from models.tipo_prodotto import TipoProdotto
from models.tipo_prodotto_valori import TipoProdottoValori
from models.tipo_prodotto_valori_dropdown import TipoProdottoValoriDropdown
from models.react_field_type import ReactFieldType
from models.scheda_tecnica_pezzo import SchedaTecnicaPezzo


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

def normalize_design(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(r"[^a-z0-9]", "", value.lower().strip())

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

    return {"fornitori": all_obj}

############################################
########### CLIENTE PROJ PARSING ###########
############################################

def extract_cliente_info(text_content, db: Session):
    lines = [line.strip() for line in text_content.split("\n")]

    cliente = {
        "nome": "",
        "citta": "",
        "indirizzo": "",
        "numero_tel": "",
        "centro_di_costo": "",
    }

    for i, line in enumerate(lines):

        if line == "COMMITTENTE" and i + 1 < len(lines):
            cliente["nome_cliente"] = lines[i + 1]

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
                cliente["centro_di_costo"] = value

        # stop when products start
        if re.match(r"^\d+\s+Infisso$", line):
            break

    existing_cliente = find_cliente_by_email(cliente["centro_di_costo"], db)
    if existing_cliente:
        cliente["id"] = existing_cliente.id
    
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

def find_cliente_by_email(email: str, db: Session):

    print('Searching for cliente with email:', email)

    if not email:
        return None

    return db.exec(
        select(Cliente).where(func.lower(Cliente.centro_di_costo) == email.lower())
    ).first()

############################################
########### Fornitore PROJ PARSING #########
############################################

def normalize_name(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()

    # remove accents: à -> a, è -> e
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))

    # remove spaces and special chars
    value = re.sub(r"[^a-z0-9]", "", value)

    return value


def add_fornitore_ids(fornitori_data: list[dict], db: Session) -> list[dict]:
    fornitori_db = db.exec(select(Fornitore.id, Fornitore.nome_cliente)).all()

    fornitori_map = {}
    for fornitore_id, nome_cliente in fornitori_db:
        nome_normalizzato = normalize_name(nome_cliente)
        fornitori_map[nome_normalizzato] = fornitore_id

    for item in fornitori_data:
        nome_pdf = item.get("Fornitore")
        nome_pdf_normalizzato = normalize_name(nome_pdf)

        ## if not found return error with fornitore name
        fornitore_id = fornitori_map.get(nome_pdf_normalizzato)
        if fornitore_id is None:
            raise HTTPException(
                status_code=400,
                detail=f"Fornitore non trovato: {nome_pdf}"
            )

        item["fornitore_id"] = fornitori_map.get(nome_pdf_normalizzato)

    return fornitori_data


############################################
########### SCHEDE TECHNICHE PROJ PARSING ##
############################################


def build_scheda_tecnica_schema_fornitore(
    fornitore_id: int,
    quantita: int,
    db: Session,
):
    fornitore_id = 13 # testing
    schemas = db.exec(
        select(SchedaTecnicaSchema).where(
            SchedaTecnicaSchema.fornitore_id == fornitore_id
        )
    ).all()

    print("fornitore_id:", fornitore_id)
    print("schemas length:", len(schemas))
    print("schemas:", schemas)

    if not schemas:
        return []

    tipo_prodotto_ids = list({s.tipo_prodotto_id for s in schemas})
    valori_ids = list({s.tipo_prodotto_valori_id for s in schemas})
    field_type_ids = list({s.field_type_id for s in schemas})

    dropdown_ids = []

    for schema in schemas:
        if schema.tipo_prodotto_dropdown_id:
            dropdown_ids.extend(schema.tipo_prodotto_dropdown_id)

    dropdown_ids = list(set(dropdown_ids))

    tipi_prodotti = db.exec(
        select(TipoProdotto).where(TipoProdotto.id.in_(tipo_prodotto_ids))
    ).all()

    valori = db.exec(
        select(TipoProdottoValori).where(TipoProdottoValori.id.in_(valori_ids))
    ).all()

    field_types = db.exec(
        select(ReactFieldType).where(ReactFieldType.id.in_(field_type_ids))
    ).all()

    dropdowns = []

    if dropdown_ids:
        dropdowns = db.exec(
            select(TipoProdottoValoriDropdown).where(
                TipoProdottoValoriDropdown.id.in_(dropdown_ids)
            )
        ).all()

    tipi_prodotti_map = {tipo.id: tipo.nome for tipo in tipi_prodotti}
    valori_map = {valore.id: valore.nome for valore in valori}
    valori_alias_map = {valore.id: valore.alias for valore in valori}
    field_types_map = {field_type.id: field_type.nome for field_type in field_types}
    dropdowns_map = {dropdown.id: dropdown for dropdown in dropdowns}

    grouped = {}

    for schema in schemas:
        tipo_id = schema.tipo_prodotto_id

        if tipo_id not in grouped:
            grouped[tipo_id] = {
                "tipo_prodotto_id": tipo_id,
                "tipo_prodotto_nome": tipi_prodotti_map.get(tipo_id),
                "quantita": quantita,
                "campi": [],
            }

        options = []

        if schema.tipo_prodotto_dropdown_id:
            for dropdown_id in schema.tipo_prodotto_dropdown_id:
                dropdown = dropdowns_map.get(dropdown_id)

                if dropdown:
                    options.append(
                        {
                            "id": dropdown.id,
                            "label": dropdown.nome,
                        }
                    )

        grouped[tipo_id]["campi"].append(
            {
                "schema_id": schema.id,
                "tipo_prodotto_valori_id": schema.tipo_prodotto_valori_id,
                "tipo_prodotto_valori": valori_map.get(schema.tipo_prodotto_valori_id),
                "tipo_prodotto_valori_alias": valori_alias_map.get(schema.tipo_prodotto_valori_id),
                "field_type_id": schema.field_type_id,
                "field_type": field_types_map.get(schema.field_type_id),
                "options": options,
            }
        )

    return list(grouped.values())


def get_schede_tecniche_fornitore(
    progetto_id: int,
    fornitore_id: int,
    db: Session,
):
    schemas = db.exec(
        select(SchedaTecnicaSchema).where(
            SchedaTecnicaSchema.fornitore_id == fornitore_id
        )
    ).all()

    if not schemas:
        return []

    tipo_prodotto_ids = list({schema.tipo_prodotto_id for schema in schemas})
    valori_ids = list({schema.tipo_prodotto_valori_id for schema in schemas})
    field_type_ids = list({schema.field_type_id for schema in schemas})
    schema_ids = [schema.id for schema in schemas]

    dropdown_ids = []

    for schema in schemas:
        if schema.tipo_prodotto_dropdown_id:
            dropdown_ids.extend(schema.tipo_prodotto_dropdown_id)

    dropdown_ids = list(set(dropdown_ids))

    tipi_prodotti = db.exec(
        select(TipoProdotto).where(TipoProdotto.id.in_(tipo_prodotto_ids))
    ).all()

    valori = db.exec(
        select(TipoProdottoValori).where(TipoProdottoValori.id.in_(valori_ids))
    ).all()

    field_types = db.exec(
        select(ReactFieldType).where(ReactFieldType.id.in_(field_type_ids))
    ).all()

    dropdowns = []

    if dropdown_ids:
        dropdowns = db.exec(
            select(TipoProdottoValoriDropdown).where(
                TipoProdottoValoriDropdown.id.in_(dropdown_ids)
            )
        ).all()

    pezzi = db.exec(
        select(SchedaTecnicaPezzo).where(
            SchedaTecnicaPezzo.progetto_id == progetto_id,
            SchedaTecnicaPezzo.scheda_tecnica_schema_id.in_(schema_ids),
        )
    ).all()

    tipi_prodotti_map = {tipo.id: tipo.nome for tipo in tipi_prodotti}
    valori_map = {valore.id: valore.nome for valore in valori}
    field_types_map = {field_type.id: field_type.nome for field_type in field_types}
    dropdowns_map = {dropdown.id: dropdown for dropdown in dropdowns}
    pezzi_map = {pezzo.scheda_tecnica_schema_id: pezzo for pezzo in pezzi}

    grouped = {}

    for schema in schemas:
        tipo_id = schema.tipo_prodotto_id

        if tipo_id not in grouped:
            grouped[tipo_id] = {
                "tipo_prodotto_id": tipo_id,
                "tipo_prodotto_nome": tipi_prodotti_map.get(tipo_id),
                "campi": [],
            }

        field_type = field_types_map.get(schema.field_type_id)

        options = []

        if schema.tipo_prodotto_dropdown_id:
            for dropdown_id in schema.tipo_prodotto_dropdown_id:
                dropdown = dropdowns_map.get(dropdown_id)

                if dropdown:
                    options.append(
                        {
                            "id": dropdown.id,
                            "label": dropdown.nome,
                        }
                    )

        pezzo = pezzi_map.get(schema.id)

        selected_value = None

        if pezzo:
            if field_type == "select":
                selected_value = next(
                    (
                        dropdown_id
                        for dropdown_id in schema.tipo_prodotto_dropdown_id
                        if dropdowns_map.get(dropdown_id)
                        and dropdowns_map[dropdown_id].nome == pezzo.valore
                    ),
                    None,
                )

            elif field_type == "number":
                selected_value = int(pezzo.valore) if pezzo.valore else None

            else:
                selected_value = pezzo.valore

        grouped[tipo_id]["campi"].append(
            {
                "tipo_prodotto_valori_id": schema.tipo_prodotto_valori_id,
                "tipo_prodotto_valori": valori_map.get(schema.tipo_prodotto_valori_id),
                "field_type": field_type,
                "options": options,
                "selected_value": selected_value,
            }
        )

    return list(grouped.values())


def enrich_schede_with_selected_values(fornitori, schede_tecniche):
    index = {}

    for fornitore_id, schede in schede_tecniche.items():
        for scheda in schede:
            key = (
                str(fornitore_id),
                normalize_design(scheda.get("tipo_prodotto_nome")),
            )

            index[key] = {
                campo["tipo_prodotto_valori_alias"]: campo
                for campo in scheda.get("campi", [])
                if campo.get("tipo_prodotto_valori_alias")
            }

    for item in fornitori:
        fornitore_id = item.get("fornitore_id")
        design = normalize_design(item.get("Design"))

        if not fornitore_id or not design:
            continue

        alias_map = index.get((str(fornitore_id), design))
        if not alias_map:
            continue

        for alias, campo in alias_map.items():
            selected_value = item.get(alias)

            if selected_value:
                campo["selected_value"] = selected_value

    return schede_tecniche
