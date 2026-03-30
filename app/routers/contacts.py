import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.config.settings import Settings, get_settings
from app.storage.azure_blob import AzureBlobStorage

router = APIRouter(prefix="/contacts", tags=["contacts"])

CONTACTS_BLOB = "contacts/contacts.json"


def get_storage(settings: Settings = Depends(get_settings)) -> AzureBlobStorage:
    return AzureBlobStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_blob_container_name,
    )


def _read_contacts(storage: AzureBlobStorage) -> dict:
    try:
        blob_client = storage._client.get_blob_client(
            container=storage._container, blob=CONTACTS_BLOB
        )
        content = blob_client.download_blob().readall()
        return json.loads(content)
    except Exception:
        return {}


def _write_contacts(storage: AzureBlobStorage, contacts: dict):
    blob_client = storage._client.get_blob_client(
        container=storage._container, blob=CONTACTS_BLOB
    )
    blob_client.upload_blob(
        json.dumps(contacts, ensure_ascii=False, indent=2).encode("utf-8"),
        overwrite=True,
    )


class ContactPayload(BaseModel):
    phone_number: str
    name: str
    note: Optional[str] = ""


@router.get("")
def list_contacts(storage: AzureBlobStorage = Depends(get_storage)):
    contacts = _read_contacts(storage)
    return {"contacts": list(contacts.values())}


@router.post("")
def save_contact(body: ContactPayload, storage: AzureBlobStorage = Depends(get_storage)):
    contacts = _read_contacts(storage)
    contacts[body.phone_number] = {
        "phone_number": body.phone_number,
        "name": body.name,
        "note": body.note or "",
    }
    _write_contacts(storage, contacts)
    return {"status": "saved", "contact": contacts[body.phone_number]}


@router.delete("/{phone_number}")
def delete_contact(phone_number: str, storage: AzureBlobStorage = Depends(get_storage)):
    contacts = _read_contacts(storage)
    if phone_number not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    del contacts[phone_number]
    _write_contacts(storage, contacts)
    return {"status": "deleted"}
