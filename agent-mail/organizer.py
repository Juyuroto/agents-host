import logging
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError

log = logging.getLogger("agent-mail")

VALID_FOLDERS = {"Urgent", "Admin", "Clients", "Factures", "Fournisseurs", "Pub"}
DEFAULT_FOLDER = "Admin"


def ensure_folder_exists(server: IMAPClient, folder: str) -> None:
    existing = [f[2] for f in server.list_folders()]
    if folder not in existing:
        server.create_folder(folder)


def move_to_folder(server: IMAPClient, uid: int, folder: str) -> None:
    if folder not in VALID_FOLDERS:
        folder = DEFAULT_FOLDER

    try:
        ensure_folder_exists(server, folder)
        server.move([uid], folder)
    except IMAPClientError:
        log.exception("Échec du déplacement du mail uid=%s vers %s", uid, folder)