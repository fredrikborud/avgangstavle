#!/usr/bin/env python3
"""
Avgangstavle med filter – som i Nå-appen.

Eksempel:
    python avgangstavle.py "Oslo S" --via Lysaker
    python avgangstavle.py "Fredrikstad" --via "Oslo S" --linje R20
    python avgangstavle.py "Lysaker" --ankomster

Datakilde: Entur JourneyPlanner v3 (åpen, ingen nøkkel). Togdataene der
kommer fra Bane NORs SIRI-strøm (datasetId BNR).
Krever: pip install requests
"""
import argparse
import sys
from datetime import datetime

import requests

CLIENT_NAME = "fredrik-avgangstavle"  # Entur ber om "firma-applikasjon"
GEOCODER = "https://api.entur.io/geocoder/v1/autocomplete"
JP = "https://api.entur.io/journey-planner/v3/graphql"
HEADERS = {"ET-Client-Name": CLIENT_NAME}

QUERY = """
query ($id: String!, $n: Int!, $range: Int!, $ad: ArrivalDeparture!) {
  stopPlace(id: $id) {
    name
    estimatedCalls(numberOfDepartures: $n, timeRange: $range,
                   arrivalDeparture: $ad,
                   whiteListedModes: [rail]) {
      aimedDepartureTime expectedDepartureTime
      aimedArrivalTime   expectedArrivalTime
      cancellation
      quay { id publicCode }
      destinationDisplay { frontText via }
      serviceJourney {
        line { publicCode authority { name } }
        quays { id stopPlace { id name } }
      }
      situations { summary { value language } }
    }
  }
}
"""


def finn_stasjon(navn: str) -> tuple[str, str]:
    """Slår opp NSR-id for en stasjon via Enturs geocoder."""
    r = requests.get(GEOCODER, headers=HEADERS, timeout=10, params={
        "text": navn, "layers": "venue", "size": 5,
        "categories": "railStation",
    })
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        sys.exit(f"Fant ingen stasjon som heter «{navn}»")
    p = feats[0]["properties"]
    return p["id"], p["name"]


def hent_kall(stop_id: str, ankomster: bool, antall: int = 60):
    r = requests.post(JP, headers=HEADERS, timeout=15, json={
        "query": QUERY,
        "variables": {
            "id": stop_id, "n": antall, "range": 4 * 3600,
            "ad": "arrivals" if ankomster else "departures",
        },
    })
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        sys.exit(f"API-feil: {data['errors']}")
    return data["data"]["stopPlace"]


def stopper_ved(call, stop_id: str, via_id: str, ankomster: bool) -> bool:
    """Sjekker om toget stopper ved via-stasjonen etter (eller før, for
    ankomster) stasjonen vi står på."""
    ids = [q["stopPlace"]["id"] for q in call["serviceJourney"]["quays"]
           if q.get("stopPlace")]
    if stop_id not in ids or via_id not in ids:
        return False
    her, via = ids.index(stop_id), ids.index(via_id)
    return via < her if ankomster else via > her


def hhmm(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%H:%M") if iso else "--:--"


def main():
    ap = argparse.ArgumentParser(description="Avgangstavle for tog")
    ap.add_argument("stasjon")
    ap.add_argument("--via", help="Vis bare tog som stopper her")
    ap.add_argument("--linje", help="F.eks. R20, L1, RE11")
    ap.add_argument("--ankomster", action="store_true")
    ap.add_argument("--antall", type=int, default=15)
    a = ap.parse_args()

    stop_id, stop_navn = finn_stasjon(a.stasjon)
    via_id = via_navn = None
    if a.via:
        via_id, via_navn = finn_stasjon(a.via)

    sp = hent_kall(stop_id, a.ankomster)
    tittel = "Ankomster" if a.ankomster else "Avganger"
    filt = f"  (via {via_navn})" if via_navn else ""
    print(f"\n{sp['name']} – {tittel}{filt}\n" + "-" * 60)

    vist = 0
    for c in sp["estimatedCalls"]:
        linje = c["serviceJourney"]["line"]["publicCode"] or ""
        if a.linje and linje.upper() != a.linje.upper():
            continue
        if via_id and not stopper_ved(c, stop_id, via_id, a.ankomster):
            continue

        if a.ankomster:
            planlagt, forventet = c["aimedArrivalTime"], c["expectedArrivalTime"]
        else:
            planlagt, forventet = c["aimedDepartureTime"], c["expectedDepartureTime"]
        forv = "" if hhmm(planlagt) == hhmm(forventet) else hhmm(forventet)
        if c["cancellation"]:
            forv = "INNSTILT"
        mål = c["destinationDisplay"]["frontText"]
        spor = c["quay"]["publicCode"] or "-"

        print(f"{hhmm(planlagt)}  {linje:<5} {mål:<22} {forv:>9}  spor {spor}")
        for s in c["situations"]:
            tekst = next((v["value"] for v in s["summary"]
                          if v.get("language") in ("no", "nob", None)),
                         s["summary"][0]["value"] if s["summary"] else "")
            if tekst:
                print(f"       ⚠ {tekst}")

        vist += 1
        if vist >= a.antall:
            break

    if not vist:
        print("Ingen tog funnet med dette filteret.")


if __name__ == "__main__":
    main()
