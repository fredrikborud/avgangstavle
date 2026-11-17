# Avgangstavle

Egen avgangstavle for tog, inspirert av Bane NORs Nå-app. Statisk side som henter sanntidsdata direkte fra Entur JourneyPlanner (togdataene kommer fra Bane NOR).

- Avganger/ankomster for valgfri stasjon
- Filter: «stopper ved» (f.eks. Oslo S → Lysaker) og linjer (R20, RE11 …)
- Favoritter lagres i nettleseren, oppdateres hvert 30. sekund
- Bokmerke-URL: `?stop=NSR:StopPlace:59872&via=<NSR-id>&lines=R20`

Hostes på GitHub Pages: Settings → Pages → Deploy from branch → `main` / root.
På iPhone: åpne siden i Safari → Del → «Legg til på Hjem-skjerm».

`avgangstavle.py` er en kommandolinjeversjon av det samme.
