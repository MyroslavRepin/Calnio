from urllib.parse import urlparse


def convert_uuid_no_dashes(uud):
    # uuid.UUID(payload["entity"]["id"])
    return uud.replace(' ', '-')


def extract_uid(url: str) -> str:
    if not url:
        return None
    url = str(url)
    path = urlparse(url).path
    return path.rstrip('/').split('/')[-1]