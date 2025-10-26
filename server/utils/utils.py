from datetime import timezone, datetime, date
from typing import Optional
from urllib.parse import urlparse


def convert_uuid_no_dashes(uud):
    # uuid.UUID(payload["entity"]["id"])
    return uud.replace(' ', '-')


def add_dashes_to_uuid(raw_uid: str) -> str:
    """
    Преобразует 32-значный hex UID в формат UUID с дефисами.
    Пример: 0868913e393a4b40ba17f8cafd8c50d7 -> 0868913e-393a-4b40-ba17-f8cafd8c50d7
    """
    if not raw_uid or len(raw_uid) != 32:
        raise ValueError("UID должен быть 32-значным hex строкой")

    return f"{raw_uid[:8]}-{raw_uid[8:12]}-{raw_uid[12:16]}-{raw_uid[16:20]}-{raw_uid[20:]}"

def extract_uid(url: str) -> Optional[str]:
    if not url:
        return None
    url = str(url)
    path = urlparse(url).path
    return path.rstrip('/').split('/')[-1]

def ensure_datetime_with_tz(dt):
    from server.app.core.logging_config import logger
    from datetime import time as time_cls

    if dt is None:
        return None

    # Parse ISO-8601 strings (handle trailing 'Z')
    if isinstance(dt, str):
        s = dt.strip()
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(s)
            logger.debug("Parsed string to datetime: %s", dt)
        except Exception as exc:
            logger.debug("Failed to parse datetime string %r: %s", dt, exc)
            raise

    # Date (without time) -> midnight of that date
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
        logger.debug("Converted date to datetime (midnight): %s", dt)

    # Time only -> combine with today's UTC date
    if isinstance(dt, time_cls):
        today_utc = datetime.now(timezone.utc).date()
        dt = datetime.combine(today_utc, dt)
        logger.debug("Combined time with today's UTC date: %s", dt)

    # At this point dt is a datetime object. Make it timezone-aware and
    # normalized to UTC. For naive datetimes we assume UTC. For aware
    # datetimes we convert them to UTC so all values are comparable.
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            logger.debug("Assigned UTC tzinfo to datetime: %s", dt)
        else:
            try:
                dt = dt.astimezone(timezone.utc)
                logger.debug("Converted aware datetime to UTC: %s", dt)
            except Exception:
                # If astimezone fails for some custom tzinfo, fall back to assigning UTC
                dt = dt.replace(tzinfo=timezone.utc)
                logger.debug("Fallback: assigned UTC tzinfo to datetime: %s", dt)

    return dt

def is_timezone_aware(dt):
    return dt is not None and dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None
