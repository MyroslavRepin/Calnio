def convert_uuid_no_dashes(uud):
    # uuid.UUID(payload["entity"]["id"])
    return uud.replace(' ', '-')