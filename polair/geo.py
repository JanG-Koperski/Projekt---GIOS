from __future__ import annotations
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from typing import Iterable, Tuple, List
from .models import Station

def geocode(q: str) -> Tuple[float, float]:
    geolocator = Nominatim(user_agent="polair_app")
    loc = geolocator.geocode(q)
    if not loc:
        raise ValueError(f"Nie znaleziono lokalizacji: {q}")
    return (loc.latitude, loc.longitude)

def nearest_within(stations: Iterable[Station], center: Tuple[float, float], radius_km: float) -> List[Station]:
    lat0, lon0 = center
    out = []
    for s in stations:
        d = geodesic((s.lat, s.lon), (lat0, lon0)).km
        if d <= radius_km:
            out.append((d, s))
    out.sort(key=lambda t: t[0])
    return [s for _, s in out]
