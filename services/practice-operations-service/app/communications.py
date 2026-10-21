"""External communication address normalization."""
import phonenumbers


class InvalidPhone(ValueError):
    pass


def normalize_phone(value: str, country_iso2: str | None = None) -> tuple[str, str]:
    raw = (value or "").strip()
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    region = None if raw.startswith("+") else (country_iso2 or "").strip().upper() or None
    if region is None and not raw.startswith("+"):
        raise InvalidPhone("A country is required for a national telephone number")
    try:
        parsed = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhone("Enter a valid telephone number") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhone("Enter a valid telephone number")
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return e164, e164[1:]
