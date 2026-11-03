import logging
from imapclient import IMAPClient

from config import IMAP_SERVER, IMAP_USER, IMAP_PASSWORD
from mailbox import parse_message
from classifier import classify_email
from notifier import notify_discord
from organizer import move_to_folder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-mail")


def process_message(server: IMAPClient, uid: int) -> None:
    raw = server.fetch([uid], ["RFC822"])[uid][b"RFC822"]
    mail = parse_message(raw)
    log.info("Nouveau mail de %s — %s", mail["sender"], mail["subject"])

    result = classify_email(mail["sender"], mail["subject"], mail["body"])
    notify_discord(
        mail["sender"],
        mail["subject"],
        result["summary"],
        result["urgency"],
        result["folder"],
    )
    move_to_folder(server, uid, result["folder"])


def run() -> None:
    log.info("Connexion IMAP à %s...", IMAP_SERVER)
    with IMAPClient(IMAP_SERVER, ssl=True) as server:
        server.login(IMAP_USER, IMAP_PASSWORD)
        server.select_folder("INBOX")
        log.info("Connecté, en écoute (IDLE)...")

        while True:
            server.idle()
            try:
                responses = server.idle_check(timeout=300)
            finally:
                server.idle_done()

            if not responses:
                continue

            uids = server.search(["UNSEEN"])
            for uid in uids:
                process_message(server, uid)
                server.add_flags(uid, [b"\\Seen"])


if __name__ == "__main__":
    run()