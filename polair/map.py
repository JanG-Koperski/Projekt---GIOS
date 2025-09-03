from __future__ import annotations
import folium


def render_map(items):
    m = folium.Map(location=[52.0, 19.0], zoom_start=6)
    for id_, name, city, lat, lon in items:
        folium.CircleMarker(
            location=[float(lat), float(lon)],
            popup=f"{name} ({city})",
            radius=6,
            color="blue",
            fill=True
        ).add_to(m)
    outfile = "map.html"
    m.save(outfile)
    return outfile
