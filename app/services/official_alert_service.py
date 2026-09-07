import time
import requests
import xml.etree.ElementTree as ET

from math import radians, sin, cos, asin, sqrt


SACHET_CAP_URL = (
    "https://sachet.ndma.gov.in/"
    "cap_public_website/FetchXMLFile"
)

SACHET_ALL_ALERTS_URL = (
    "https://sachet.ndma.gov.in/"
    "cap_public_website/FetchAllAlertDetails"
)

SACHET_RSS_URL = (
    "https://sachet.ndma.gov.in/"
    "cap_public_website/rss/rss_india.xml"
)


_cached_xml = None
_cached_etag = None

_cached_alerts = None
_cached_alerts_at = 0

CACHE_TTL = 60


# ---------------------------------------------------------
# XML helper
# ---------------------------------------------------------

def get_text(root, tag):
    element = root.find(".//" + tag)

    if element is not None and element.text:
        return element.text.strip()

    return ""


# ---------------------------------------------------------
# Parse CAP alert
# ---------------------------------------------------------

def parse_alert(xml_text):

    if not xml_text:
        return None

    try:
        root = ET.fromstring(xml_text)

    except ET.ParseError:
        return None

    info = root.find(".//info")

    if info is None:
        return None

    alert = {
        "identifier": get_text(root, "identifier"),
        "sender": get_text(root, "sender"),
        "sent": get_text(root, "sent"),
        "status": get_text(root, "status"),
        "msg_type": get_text(root, "msgType"),

        "event": get_text(info, "event"),
        "headline": get_text(info, "headline"),
        "description": get_text(info, "description"),
        "instruction": get_text(info, "instruction"),

        "severity": get_text(info, "severity"),
        "urgency": get_text(info, "urgency"),
        "certainty": get_text(info, "certainty"),

        "effective": get_text(info, "effective"),
        "onset": get_text(info, "onset"),
        "expires": get_text(info, "expires"),

        "area": []
    }

    for area in info.findall(".//area"):

        alert["area"].append({
            "area_desc": get_text(
                area,
                "areaDesc"
            ),

            "polygon": get_text(
                area,
                "polygon"
            ),

            "circle": get_text(
                area,
                "circle"
            ),

            "geocode": [
                {
                    "name": x.findtext(
                        "valueName",
                        ""
                    ),

                    "value": x.findtext(
                        "value",
                        ""
                    )
                }

                for x in area.findall(
                    ".//geocode"
                )
            ]
        })

    return alert


# ---------------------------------------------------------
# Get individual official alert
# ---------------------------------------------------------

def get_official_alerts(identifier):

    global _cached_xml
    global _cached_etag

    try:

        headers = {}

        if _cached_etag:
            headers["If-None-Match"] = _cached_etag

        response = requests.get(
            SACHET_CAP_URL,
            params={
                "identifier": identifier
            },
            headers=headers,
            timeout=15
        )

        if response.status_code == 304:

            return {
                "success": True,
                "status": "not_modified",
                "source": "NDMA SACHET",
                "alert": parse_alert(
                    _cached_xml
                )
            }

        response.raise_for_status()

        _cached_xml = response.text

        _cached_etag = response.headers.get(
            "ETag"
        )

        alert = parse_alert(
            _cached_xml
        )

        if alert is None:

            return {
                "success": False,
                "source": "NDMA SACHET",
                "message":
                    "Official alert data could not be parsed."
            }

        return {
            "success": True,
            "status": "updated",
            "source": "NDMA SACHET",
            "etag": _cached_etag,
            "alert": alert
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "source": "NDMA SACHET",
            "message":
                "Unable to retrieve official alert data.",
            "error": str(exc)
        }


# ---------------------------------------------------------
# Normalize alert
# ---------------------------------------------------------

def _norm(item):

    if not isinstance(item, dict):
        return None

    identifier = str(
        item.get("identifier")
        or item.get("id")
        or ""
    )

    if not identifier:
        return None

    return {
        "identifier": identifier,

        "severity":
            item.get("severity")
            or item.get("severity_level")
            or "",

        "severity_color":
            item.get("severity_color")
            or "",

        "effective":
            item.get("effective_start_time")
            or item.get("effective")
            or "",

        "expires":
            item.get("effective_end_time")
            or item.get("expires")
            or "",

        "event":
            item.get("disaster_type")
            or item.get("event")
            or "",

        "area_desc":
            item.get("area_description")
            or item.get("areaDesc")
            or "",

        "headline":
            item.get("warning_message")
            or item.get("headline")
            or "",

        "sender":
            item.get("alert_source")
            or item.get("sender")
            or "",

        "language":
            item.get("actual_lang")
            or item.get("language")
            or "",

        "centroid":
            item.get("centroid")
            or "",

        "area_covered":
            item.get("area_covered"),

        "raw": item
    }


# ---------------------------------------------------------
# Fetch active alerts
# ---------------------------------------------------------

def _fetch():

    global _cached_alerts
    global _cached_alerts_at

    if (
        _cached_alerts is not None
        and
        time.monotonic() - _cached_alerts_at
        < CACHE_TTL
    ):

        return _cached_alerts, True

    # -----------------------------------------------------
    # Primary SACHET endpoint
    # -----------------------------------------------------

    try:

        response = requests.get(
            SACHET_ALL_ALERTS_URL,
            timeout=15
        )

        response.raise_for_status()

        payload = response.json()

        if isinstance(payload, list):

            alerts = [
                _norm(item)
                for item in payload
            ]

            alerts = [
                item
                for item in alerts
                if item is not None
            ]

            _cached_alerts = alerts
            _cached_alerts_at = time.monotonic()

            return alerts, False

    except (
        requests.RequestException,
        ValueError
    ):
        pass

    # -----------------------------------------------------
    # RSS fallback
    # -----------------------------------------------------

    try:

        response = requests.get(
            SACHET_RSS_URL,
            timeout=15
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.text
        )

        alerts = []

        for item in root.findall(
            ".//item"
        ):

            raw = {
                child.tag.split("}")[-1]:
                    child.text or ""

                for child in item
            }

            alert = _norm(raw)

            if alert:
                alerts.append(alert)

        _cached_alerts = alerts
        _cached_alerts_at = time.monotonic()

        return alerts, False

    except (
        requests.RequestException,
        ET.ParseError
    ) as exc:

        raise RuntimeError(
            "Unable to retrieve the NDMA SACHET active-alert feed"
        ) from exc


# ---------------------------------------------------------
# Distance calculation
# ---------------------------------------------------------

def _distance_km(
    latitude,
    longitude,
    centroid
):

    try:

        lon, lat = map(
            float,
            centroid.split(",")[:2]
        )

    except (
        AttributeError,
        TypeError,
        ValueError
    ):

        return None

    earth_radius = 6371.0088

    dlon = radians(
        lon - longitude
    )

    dlat = radians(
        lat - latitude
    )

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(latitude))
        *
        cos(radians(lat))
        *
        sin(dlon / 2) ** 2
    )

    return (
        2
        *
        earth_radius
        *
        asin(
            sqrt(
                max(
                    0,
                    min(1, a)
                )
            )
        )
    )


# ---------------------------------------------------------
# Public active alert function
# ---------------------------------------------------------

def get_active_official_alerts(
    latitude=None,
    longitude=None,
    radius_km=None,
    limit=50
):

    alerts, cached = _fetch()

    if latitude is not None:

        filtered = []

        for alert in alerts:

            distance = _distance_km(
                latitude,
                longitude,
                alert.get("centroid")
            )

            alert_copy = dict(alert)

            alert_copy["distance_km"] = (
                round(distance, 1)
                if distance is not None
                else None
            )

            if (
                distance is None
                or distance <= radius_km
            ):
                filtered.append(
                    alert_copy
                )

        alerts = filtered

    alerts = alerts[:limit]

    return {
        "success": True,

        "source":
            "NDMA SACHET",

        "cached":
            cached,

        "count":
            len(alerts),

        "alerts":
            alerts,

        "official_note":
            "Use official SACHET/IMD warnings "
            "for operational decisions."
    }