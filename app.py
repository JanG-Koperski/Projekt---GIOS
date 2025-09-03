from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import webbrowser
import os
from polair.utils import get_logger
from polair import api, db, repository as repo, services, plotting, map as mapmod

logger = get_logger(__name__)

class PolAirApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Program do Jakości Powietrza")
        self.geometry("1050x800")
        self.conn = db.get_conn()
        db.init_db(self.conn)
        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook.Tab",
                        padding=[20, 5],  # [szerokość, wysokość]
                        font=("Arial", 12, "bold"))  # większa czcionka
        style.configure("Treeview.Heading",
                        font=("Arial", 9, "bold"),  # większa czcionka
                        padding=[5, 2])

        self.tab_stations = ttk.Frame(notebook)
        self.tab_measure = ttk.Frame(notebook)
        notebook.add(self.tab_stations, text="Stacje")
        notebook.add(self.tab_measure, text="Pomiary i wykres")

        style = ttk.Style()
        style.configure("TButton", foreground="blue", padding=[20, 5], font=("Arial", 12, "bold"))

        # --- Tab Stations
        frm = ttk.Frame(self.tab_stations, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        top = ttk.Frame(frm)
        top.pack(fill=tk.X)
        self.city_var = tk.StringVar()
        ttk.Label(top, text="Miasto:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.city_var, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Pobierz stacje (REST)", command=self.fetch_stations).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Filtruj z bazy", command=self.load_stations_from_db).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Mapa", command=self.open_map).pack(side=tk.LEFT, padx=4)

        self.tree = ttk.Treeview(frm, columns=("id", "name", "city", "gmina", "powiat", "wojew", "lat", "lon"), show="headings")
        for col, label, w in [("id","ID",35),("name","Nazwa",250),("city","Miasto",130), ("gmina","Gmina",130), ("powiat","Powiat",130),("wojew","Województwo",150), ("lat","X",80),("lon","Y",80)]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=w, anchor=tk.W, stretch=False)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=8)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Zapisz stacje do bazy", command=self.save_stations).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Pobierz czujniki stacji", command=self.fetch_sensors_for_selected).pack(side=tk.LEFT, padx=4)

        # --- Tab Measure
        frm2 = ttk.Frame(self.tab_measure, padding=8)
        frm2.pack(fill=tk.BOTH, expand=True)

        # Górna część: ID stacji i czujnika
        top2 = ttk.Frame(frm2)
        top2.pack(fill=tk.X, pady=(0, 5))
        self.station_id_var = tk.StringVar()
        self.sensor_id_var = tk.StringVar()

        ttk.Label(top2, text="ID stacji:").pack(side=tk.LEFT)
        ttk.Entry(top2, textvariable=self.station_id_var, width=10).pack(side=tk.LEFT, padx=4)
        ttk.Button(top2, text="Załaduj czujniki z bazy", command=self.load_sensors_from_db).pack(side=tk.LEFT, padx=4)

        ttk.Label(top2, text="ID czujnika:").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Entry(top2, textvariable=self.sensor_id_var, width=10).pack(side=tk.LEFT, padx=4)
        ttk.Button(top2, text="Pomiary (REST)", command=self.fetch_measurements).pack(side=tk.LEFT, padx=4)
        ttk.Button(top2, text="Zapisz pomiary do bazy", command=self.save_measurements).pack(side=tk.LEFT, padx=4)

        self.sensors_tree = ttk.Treeview(frm2, columns=("id", "code", "name"), show="headings", height=6)
        for col, label, w in [("id", "ID", 60), ("code", "Kod", 90), ("name", "Nazwa", 150)]:
            self.sensors_tree.heading(col, text=label)
            self.sensors_tree.column(col, width=w, anchor=tk.W, stretch=False)
        self.sensors_tree.pack(fill=tk.X, pady=8)
        self.sensors_tree.bind("<<TreeviewSelect>>", self.on_sensor_selected)


        # --- Środkowa część: tabele obok siebie
        tables_frame = ttk.Frame(frm2)
        tables_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        tables_frame.grid_columnconfigure(0, weight=3, uniform="tables")
        tables_frame.grid_columnconfigure(1, weight=8, uniform="tables")

        # Nagłówki nad tabelami
        ttk.Label(tables_frame, text="Dane pomiarowe", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="nsew", pady=(0, 2)
        )
        ttk.Label(tables_frame, text="Indeks Powietrza", font=("Arial", 10, "bold")).grid(
            row=0, column=1, sticky="nsew", pady=(0, 2)
        )

        # Lewa tabela (pomiary) - 1/3 szerokości
        self.measure_tree = ttk.Treeview(tables_frame, columns=("date", "value"), show="headings", height=15)
        self.measure_tree.heading("date", text="Data")
        self.measure_tree.heading("value", text="Wartość")
        self.measure_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=5)
        self.measure_tree.column("date", width=120, anchor=tk.E)
        self.measure_tree.column("value", width=60, anchor=tk.E)

        # Prawa tabela (indeks powietrza) - 2/3 szerokości
        self.aqindex_tree = ttk.Treeview(tables_frame, columns=("station_id", "category", "value", "calc_date", "critical"), show="headings", height=10)
        self.aqindex_tree.heading("station_id", text="Wartość indeksu dla wskaźnika")
        self.aqindex_tree.heading("category", text="Kategoria")
        self.aqindex_tree.heading("value", text="Wartość")
        self.aqindex_tree.heading("calc_date", text="Data obliczeń")
        # self.aqindex_tree.heading("critical", text="Zanieczyszczenie krytyczne")
        self.aqindex_tree.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=5)
        self.aqindex_tree.column("station_id", width=50, anchor=tk.E)
        self.aqindex_tree.column("category", width=50, anchor=tk.E)
        self.aqindex_tree.column("value", width=70, anchor=tk.E)
        self.aqindex_tree.column("calc_date", width=120, anchor=tk.E)
        self.aqindex_tree.column("critical", width=150, anchor=tk.E)

        # --- Dolna część: przyciski pod tabelami
        buttons_frame = ttk.Frame(frm2)
        buttons_frame.pack(fill=tk.X, pady=5)
        ttk.Button(buttons_frame, text="Wykres", command=self.plot_measurements).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons_frame, text="Analiza", command=self.analyze_measurements).pack(side=tk.LEFT, padx=4)
        self.status = tk.StringVar(value="Gotowe")
        ttk.Label(self, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    # --- Actions
    def set_status(self, text: str):
        self.status.set(text)
        self.update_idletasks()

    def threaded(self, fn):
        def wrapper():
            t = threading.Thread(target=fn, daemon=True)
            t.start()
        return wrapper

    @property
    def selected_station_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0])["values"]
        return int(vals[0])

    def fetch_stations(self):
        @self.threaded
        def worker():
            try:
                self.set_status("Pobieranie stacji...")
                items = list(api.iter_all_stations())
                stations = [services.parse_station(r) for r in items]
                self._stations_cache = stations
                self.tree.delete(*self.tree.get_children())
                city_filter = self.city_var.get().strip()
                for s in stations:
                    if city_filter and (s.city_name or "").lower().find(city_filter.lower()) < 0:
                        continue
                    self.tree.insert("", tk.END, values=(s.id, s.name, s.city_name, s.commune, s.district, s.province, s.lat, s.lon))
                self.set_status(f"Pobrano {len(stations)} stacji (filtrowane: {city_filter or '—'})")
            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać danych z API. Możesz skorzystać z danych z bazy.\n\n{e}")
                self.set_status("Błąd pobierania (API)")
        worker()

    def load_stations_from_db(self):
        city_filter = self.city_var.get().strip()
        stations = repo.get_stations(self.conn, city_filter or None)
        self.tree.delete(*self.tree.get_children())
        for s in stations:
            vals = (
                getattr(s, "id", "") or "",
                getattr(s, "name", "") or "",
                getattr(s, "city_name", "") or getattr(s, "city", "") or "",
                getattr(s, "commune", "") or "",
                getattr(s, "district", "") or "",
                getattr(s, "province", "") or "",
                getattr(s, "lat", "") or "",
                getattr(s, "lon", "") or "",
            )
            self.tree.insert("", tk.END, values=vals)
        self.set_status(f"Załadowano {len(stations)} stacji z bazy")

    def save_stations(self):
        if not hasattr(self, "_stations_cache"):
            messagebox.showinfo("Info", "Najpierw pobierz stacje z REST.")
            return
        repo.upsert_stations(self.conn, self._stations_cache)
        self.set_status("Zapisano stacje do bazy.")

    def fetch_sensors_for_selected(self):
        sid = self.selected_station_id
        if not sid:
            messagebox.showinfo("Info", "Zaznacz stację na liście.")
            return

        @self.threaded
        def worker():
            import sqlite3
            try:
                self.set_status("Pobieranie czujników...")
                recs = api.get_sensors(sid)
                sensors = [services.parse_sensor(r) for r in recs]
                conn = sqlite3.connect("polair.db")
                repo.ensure_schema(conn)
                repo.upsert_sensors(conn, sensors)
                conn.close()

                self.sensors_tree.delete(*self.sensors_tree.get_children())
                for s in sensors:
                    self.sensors_tree.insert("", tk.END, values=(s.id, s.param_code, s.param_name))
                self.station_id_var.set(str(sid))
                self.set_status(f"Pobrano {len(sensors)} czujników dla stacji {sid}")

                self.after(0, lambda: self.tab_measure.master.select(self.tab_measure))
            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać czujników.\n\n{e}")
                self.set_status("Błąd pobierania czujników")

                # Parsowanie JSON
                if isinstance(recs, str):
                    import json
                    try:
                        recs = json.loads(recs)
                    except json.JSONDecodeError:
                        messagebox.showwarning(
                            "Błąd", "Nieprawidłowy format danych z API"
                        )
                        self.set_status("Błąd pobierania czujników")
                        return

                # Tworzymy listę obiektów sensorów
                recs = api.get_sensors(sid)  # <- teraz to jest LISTA słowników
                sensors = [services.parse_sensor(r) for r in recs]

                # Aktualizacja bazy i widoku
                repo.upsert_sensors(self.conn, sensors)
                self.sensors_tree.delete(*self.sensors_tree.get_children())
                for s in sensors:
                    self.sensors_tree.insert("", tk.END, values=(s.id, s.param_code, s.param_name))
                self.station_id_var.set(str(sid))
                self.set_status(f"Pobrano {len(sensors)} czujników dla stacji {sid}")

            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać czujników.\n\n{e}")
                self.set_status("Błąd pobierania czujników")
        worker()

    def load_sensors_from_db(self):
        sid = self.station_id_var.get().strip()
        if not sid.isdigit():
            messagebox.showinfo("Info", "Podaj poprawny ID stacji (liczba).")
            return
        sensors = repo.get_sensors_by_station(self.conn, int(sid))
        self.sensors_tree.delete(*self.sensors_tree.get_children())
        for s in sensors:
            self.sensors_tree.insert("", tk.END, values=(s.id, s.param_code, s.param_name))

    def fetch_measurements(self):
        sid = self.sensor_id_var.get().strip()
        ms = api.get_measurements(int(sid))
        self._measure_cache = ms
        station_id = self.selected_station_id  # potrzebne do pobrania indeksu
        if not sid.isdigit():
            messagebox.showinfo("Info", "Podaj poprawny ID czujnika (liczba).")
            return

        def _update_measurements_table(rows, sid,  save_to_db=False):
            """Aktualizuje tabelę pomiarów i cache dla wszystkich przypadków (archiwum i bieżące dane)."""
            from types import SimpleNamespace
            from datetime import datetime

            self.measure_tree.delete(*self.measure_tree.get_children())
            self.aqindex_tree.delete(*self.aqindex_tree.get_children())  # wyczyść indeks powietrza przy archiwum

            cache = []
            inserted = 0
            for r in rows:
                dt_str = r.get("Data")
                val = r.get("Wartość")
                if val is None:
                    val = ""

                self.measure_tree.insert("", "end", values=(dt_str, val))

                # cache
                try:
                    dt_py = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") if dt_str else None
                except Exception:
                    dt_py = None

                cache.append(SimpleNamespace(sensor_id=int(sid), dt=dt_py, value=val))
                inserted += 1

            self._measure_cache = cache

            if save_to_db and cache:
                repo.upsert_measurements(self.conn, cache)

            return inserted

        @self.threaded
        def worker():
            from datetime import datetime, timedelta
            import requests

            try:
                self.set_status("Pobieranie pomiarów (REST)...")
                rows = api.get_measurements(int(sid))
                ms = services.parse_measurements(rows, int(sid))

                # --- obsługa błędów API ---
                # --- Błąd API: brak bieżących danych ---
                # --- Błąd API: brak bieżących danych ---
                if isinstance(rows, dict) and "error_result" in rows:
                    messagebox.showinfo("Brak danych", "Brak wartości - należy skorzystać z archiwum")
                    self.set_status("Pobieranie danych archiwalnych...")

                    # początkowo 5 tygodni wstecz
                    date_to = datetime.now()
                    date_from = date_to - timedelta(weeks=5)
                    for weeks_back in (5, 10):
                        date_from = date_to - timedelta(weeks=weeks_back)
                        url = (
                            f"https://api.gios.gov.pl/pjp-api/v1/rest/archivalData/getDataBySensor/"
                            f"{sid}?page=0&size=30&dateFrom={date_from.strftime('%Y-%m-%d')}%2000%3A00"
                            f"&dateTo={date_to.strftime('%Y-%m-%d')}%2000%3A00"
                        )
                        archival = requests.get(url).json()
                        rows = archival.get("Lista archiwalnych wyników pomiarów", [])
                        if rows:
                            break  # znaleziono dane, kończymy pętlę

                    if not rows:
                        messagebox.showinfo("Brak danych", "Brak wartości w archiwum")
                        self.set_status("Brak danych archiwalnych")
                        return

                    inserted = _update_measurements_table(rows, sid)
                    self.set_status(f"Pobrano {inserted} archiwalnych pomiarów")
                    return

                # --- normalne dane bieżące ---
                if isinstance(rows, dict):
                    rows = rows.get("Lista danych pomiarowych", []) or []

                if not rows or all(r.get("Wartość") in (None, "") for r in rows):
                    messagebox.showinfo("Brak danych", "Brak wartości - należy skorzystać z archiwum")
                    self.set_status("Brak danych bieżących")
                    return

                inserted = _update_measurements_table(rows, sid)

                # Indeks powietrza
                idx_data = api.get_air_index(int(sid))
                aq = idx_data.get("AqIndex")
                if isinstance(aq, list) and len(aq) > 0:
                    aq = aq[0]
                from polair.models import AirIndex
                indexes = []

                for key, val in aq.items():
                    if key.startswith("Wartość indeksu dla wskaźnika"):
                        param = key.split("dla wskaźnika ")[-1]
                        value = val
                        cat_key = f"Nazwa kategorii indeksu dla wskażnika {param}"
                        category = aq.get(cat_key)
                        date_key = f"Data wykonania obliczeń indeksu dla wskaźnika {param}"
                        calc_date = aq.get(date_key)
                        calc_dt = datetime.fromisoformat(calc_date) if calc_date else None
                        indexes.append(AirIndex(station_id=station_id, param=param, value=value, category=category, calc_date=calc_dt))

                self._index_cache = indexes
                self.aqindex_tree.delete(*self.aqindex_tree.get_children())
                for i in indexes:
                    self.aqindex_tree.insert("", tk.END, values=(i.value, i.param, i.category, i.calc_date.isoformat(sep=" ", timespec="minutes") if i.calc_date else ""))

                count = len(ms)
                self.set_status(f"Pobrano {count} pomiarów i indeks powietrza")

            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać pomiarów lub indeksu.\n\n{e}")
                self.set_status("Błąd pobierania")

                from types import SimpleNamespace
                from datetime import datetime
                cache = []
                for r in rows:
                    dt_str = r.get("Data")
                    try:
                        dt_py = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") if dt_str else None
                    except Exception:
                        dt_py = None
                    cache.append(SimpleNamespace(
                        sensor_id=int(sid),
                        dt=dt_py,
                        value=r.get("Wartość")
                    ))
                self._measure_cache = cache
                self.set_status(f"Pobrano {inserted} pomiarów dla sensora {sid}")
            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać pomiarów.\n\n{e}")
                self.set_status("Błąd pobierania pomiarów")
        worker()

    def fetch_measurements_for_selected(self):
        sid = getattr(self, "selected_sensor_id", None)
        if not sid:
            messagebox.showinfo("Info", "Zaznacz czujnik na liście.")
            return

        @self.threaded
        def worker():
            try:
                self.set_status("Pobieranie pomiarów (REST)...")
                rows = api.get_measurements(int(sid))
                ms = services.parse_measurements(rows, int(sid))
                if isinstance(rows, dict):
                    rows = rows.get("Lista danych pomiarowych", []) or []

                self.measure_tree.delete(*self.measure_tree.get_children())
                inserted = 0
                for r in rows:
                    dt = r.get("Data", "")
                    val = r.get("Wartość", "")
                    if val is None:
                        val = ""
                    self.measure_tree.insert("", "end", values=(dt, val))
                    inserted += 1

                from types import SimpleNamespace
                from datetime import datetime
                cache = []
                for r in rows:
                    dt_str = r.get("Data")
                    try:
                        dt_py = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") if dt_str else None
                    except Exception:
                        dt_py = None
                    cache.append(SimpleNamespace(
                        sensor_id=int(sid),
                        dt=dt_py,
                        value=r.get("Wartość")
                    ))
                self._measure_cache = cache
                self._measure_cache = ms
                self.set_status(f"Pobrano {inserted} pomiarów dla sensora {sid}")
            except Exception as e:
                messagebox.showwarning("Błąd", f"Nie udało się pobrać pomiarów.\n\n{e}")
                self.set_status("Błąd pobierania pomiarów")

        worker()

    def save_measurements(self):
        if not hasattr(self, "_measure_cache") or not self._measure_cache:
            messagebox.showinfo("Info", "Najpierw pobierz pomiary.")
            return
        repo.upsert_measurements(self.conn, self._measure_cache)
        self.set_status("Zapisano pomiary do bazy.")

    def _get_measurements_from_cache(self):

        raw = getattr(self, "_measure_cache", None)
        if not raw:
            return []

        out = []
        for item in raw:

            if isinstance(item, dict):
                dt_raw = item.get("dt") or item.get("Data") or item.get("date") or item.get("Date")
                val_raw = (item.get("value") if "value" in item else
                           item.get("Wartość") if "Wartość" in item else
                           item.get("val") if "val" in item else None)
                sid = item.get("sensor_id") or item.get("sensorId") or item.get("id")
            else:
                dt_raw = getattr(item, "dt", None)
                val_raw = getattr(item, "value", None) if getattr(item, "value", None) is not None else getattr(item,"val",None)
                sid = getattr(item, "sensor_id", None) or getattr(item, "sensorId", None) or getattr(item, "id", None)

            # konwersja daty
            dt_parsed = None
            if isinstance(dt_raw, datetime):
                dt_parsed = dt_raw
            elif isinstance(dt_raw, str):
                # próbujemy kilka formatów
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        dt_parsed = datetime.fromisoformat(dt_raw)
                        break
                    except Exception:
                        try:
                            dt_parsed = datetime.strptime(dt_raw, fmt)
                            break
                        except Exception:
                            dt_parsed = None

            # wartość jako float
            val = None
            if val_raw is not None:
                try:
                    val = float(val_raw)
                except Exception:
                    val = None

            out.append({"dt": dt_parsed, "value": val, "sensor_id": sid})

        # sortujemy rosnąco wg daty i zwracamy tylko te z datą
        out = [r for r in out if r["dt"] is not None]
        out.sort(key=lambda x: x["dt"])
        return out

    def plot_measurements(self):

        ms = self._get_measurements_from_cache()
        if not ms:
            messagebox.showinfo("Info", "Najpierw pobierz pomiary.")
            return

        xs = [r["dt"] for r in ms if r["value"] is not None]
        ys = [r["value"] for r in ms if r["value"] is not None]
        if not xs:
            messagebox.showinfo("Info", "Brak wartości liczbowych do wyświetlenia na wykresie.")
            return

        try:
            import matplotlib.pyplot as plt
        except Exception as e:
            messagebox.showerror("Błąd", f"Brak biblioteki matplotlib: {e}\nZainstaluj ją: pip install matplotlib")
            return

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(xs, ys, marker="o", linestyle="-")
        ax.set_title(f"Wykres pomiarów — czujnik {self.sensor_id_var.get() or ''}")
        ax.set_xlabel("Czas")
        ax.set_ylabel("Wartość")
        fig.autofmt_xdate()

        # zapisz do pliku tymczasowego i otwórz
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            fig.savefig(tmp, bbox_inches="tight")
            try:
                import webbrowser, os
                webbrowser.open(f"file://{os.path.abspath(tmp)}")
            except Exception:
                pass
        except Exception as e:
            messagebox.showwarning("Uwaga", f"Wykres wygenerowany, ale nie udało się zapisać/otworzyć pliku: {e}")
        finally:
            plt.close(fig)

    def analyze_measurements(self):

        ms = self._get_measurements_from_cache()
        if not ms:
            messagebox.showinfo("Info", "Najpierw pobierz pomiary.")
            return

        vals = [(r["dt"], r["value"]) for r in ms if r["value"] is not None]
        if not vals:
            messagebox.showinfo("Info", "Brak wartości liczbowych do analizy.")
            return

        dates = [d for d, v in vals]
        values = [v for d, v in vals]

        # min/max
        min_v = min(values)
        max_v = max(values)
        # find times
        min_at = next(d for d, v in vals if v == min_v)
        max_at = next(d for d, v in vals if v == max_v)
        avg = sum(values) / len(values)

        # trend: regresja liniowa (slope) na timestamp -> wartości
        xs = [d.timestamp() for d in dates]
        ys = values
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        den = sum((xs[i] - mean_x) ** 2 for i in range(n))
        slope = (num / den) if den != 0 else 0.0

        # formatowanie wyników
        msg = (
            f"Min: {min_v} o {min_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Max: {max_v} o {max_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Średnia: {avg:.2f}\n"
            f"Trend (nachylenie): {slope:.6f} (jednostka: wartość / sekunda)"
        )
        messagebox.showinfo("Analiza pomiarów", msg)


    def open_map(self):
        # pobieramy wszystkie wiersze w drzewku
        all_items = self.tree.get_children()
        items = []

        for iid in all_items:
            values = self.tree.item(iid)["values"]
            try:
                id_ = values[0]
                name = values[1]
                city = values[2]
                lat = float(values[-2])  # przedostatnia kolumna
                lon = float(values[-1])  # ostatnia kolumna
                items.append((id_, name, city, lat, lon))
            except Exception as e:
                print("Błąd przy parsowaniu współrzędnych:", e, values)
                continue

        if not items:
            messagebox.showinfo("Mapa", "Brak stacji do pokazania na mapie")
            return

        outfile = mapmod.render_map(items)
        webbrowser.open(f"file://{os.path.abspath(outfile)}")

    def on_sensor_selected(self, event):
        sel = self.sensors_tree.selection()
        if sel:
            item = self.sensors_tree.item(sel[0])
            sensor_id = item["values"][0]  # zakładamy, że pierwsza kolumna to ID
            self.sensor_id_var.set(str(sensor_id))

if __name__ == "__main__":
    app = PolAirApp()
    app.mainloop()
