from fastapi import APIRouter, Depends
from sqlmodel import Session, select
import sys
import os

from dependecies import get_db

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from models.scheda_tecnica_pezzo import SchedaTecnicaPezzo
from models.scheda_tecnica_schema import SchedaTecnicaSchema
from models.tipo_prodotto import TipoProdotto
from models.tipo_prodotto_valori import TipoProdottoValori
from models.tipo_prodotto_valori_dropdown import TipoProdottoValoriDropdown
from models.react_field_type import ReactFieldType

router = APIRouter()


@router.get("/{progetto_id}/{fornitore_id}")
def get_schede_tecniche_fornitore(
    progetto_id: int,
    fornitore_id: int,
    db: Session = Depends(get_db),
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
        )
    ).all()

    tipi_prodotti_map = {tipo.id: tipo.nome for tipo in tipi_prodotti}
    valori_map = {valore.id: valore.nome for valore in valori}
    field_types_map = {field_type.id: field_type.nome for field_type in field_types}
    dropdowns_map = {dropdown.id: dropdown for dropdown in dropdowns}
    pezzi_map = {pezzo.scheda_tecnica_schema_id: pezzo.valore for pezzo in pezzi}

    grouped = {}

    for schema in schemas:
        tipo_id = schema.tipo_prodotto_id

        if tipo_id not in grouped:
            grouped[tipo_id] = {
                "tipo_prodotto_id": tipo_id,
                "tipo_prodotto_nome": tipi_prodotti_map.get(tipo_id),
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
                            "value": dropdown.nome,
                        }
                    )

        grouped[tipo_id]["campi"].append(
            {
                "tipo_prodotto_valori_id": schema.tipo_prodotto_valori_id,
                "tipo_prodotto_valori": valori_map.get(
                    schema.tipo_prodotto_valori_id
                ),
                "field_type": field_types_map.get(schema.field_type_id),
                "options": options,
                "selected_value": pezzi_map.get(schema.id),
            }
        )

    return list(grouped.values())
