import email
from email.header import decode_header
from email.message import Message


def decode_mime(value: str) -> str:

    if not value:
        return ""
    parts = decode_header(value)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out


def get_body(msg: Message) -> str:

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get("Content-Disposition", "")
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="ignore")
        return "(pas de contenu texte trouvé)"

    payload = msg.get_payload(decode=True)
    if not payload:
        return "(mail vide)"
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="ignore")


def parse_message(raw: bytes) -> dict:

    msg = email.message_from_bytes(raw)
    return {
        "sender": decode_mime(msg.get("From", "inconnu")),
        "subject": decode_mime(msg.get("Subject", "(sans sujet)")),
        "body": get_body(msg),
    }