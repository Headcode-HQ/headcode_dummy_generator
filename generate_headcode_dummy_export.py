#!/usr/bin/env python3
"""
Generate a realistic 3+ year Headcode FULL export dummy dataset.

Outputs:
- spots.csv (exact FULL export CSV schema from SpotLogModel._csvHeaderRow)
- classes.csv
- types.csv
- conditions.csv
- locations.csv
- operators.csv
- locomotive_details.csv
- reference/classes.json
- reference/types.json
- reference/conditions.json
- reference/locations.json
- reference/operators.json
- reference/locomotive_details.json

Default output directory:
  dummy_data/headcode_full_export_3y
"""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import queue
import random
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except Exception:
    tk = None
    filedialog = None
    messagebox = None
    ttk = None
    ScrolledText = None


def normalize(value: str) -> str:
    return value.strip().lower()


def iso_local(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000")


def iso_utc(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_dataset(output_dir: Path, seed: int) -> dict[str, int]:
    random.seed(seed)

    ref_dir = output_dir / "reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    ref_dir.mkdir(parents=True, exist_ok=True)

    classes = [
        "Class 37",
        "Class 47",
        "Class 57",
        "Class 66",
        "Class 67",
        "Class 68",
        "Class 90",
        "Class 91",
        "Class 158",
        "Class 170",
        "Class 220",
        "Class 800",
        "Class 802",
    ]

    class_type = {
        "Class 37": "Diesel",
        "Class 47": "Diesel",
        "Class 57": "Diesel",
        "Class 66": "Diesel-Electric",
        "Class 67": "Diesel-Electric",
        "Class 68": "Diesel-Electric",
        "Class 90": "Electric",
        "Class 91": "Electric",
        "Class 158": "DMU/EMU",
        "Class 170": "DMU/EMU",
        "Class 220": "DMU/EMU",
        "Class 800": "Hybrid",
        "Class 802": "Hybrid",
    }

    types = [
        "Steam",
        "Diesel",
        "Electric",
        "Diesel-Electric",
        "Battery-Electric",
        "Hybrid",
        "DMU/EMU",
        "Bi-mode",
    ]
    conditions = ["Gleaming", "Clean", "Fair", "Dirty", "Filthy beast", "Weathered"]

    operators = [
        ("DB Cargo UK", False),
        ("Freightliner", False),
        ("GB Railfreight", False),
        ("Direct Rail Services", False),
        ("Colas Rail", False),
        ("West Coast Railways", False),
        ("Network Rail", False),
        ("LNER", False),
        ("CrossCountry", False),
        ("Avanti West Coast", False),
        ("Northern", False),
        ("ScotRail", False),
        ("TransPennine Express", False),
        ("Great Western Railway", False),
        ("East Midlands Railway", False),
        ("Chiltern Railways", False),
        ("Caledonian Sleeper", False),
        ("Rail Operations Group", True),
        ("Vintage Trains", True),
        ("Hanson & Hall Railtour", True),
    ]

    locations = [
        ("York", False, 53.9583, -1.0931),
        ("Doncaster", False, 53.5228, -1.1398),
        ("Peterborough", False, 52.5734, -0.2506),
        ("Crewe", False, 53.0890, -2.4320),
        ("Preston", False, 53.7553, -2.7085),
        ("Carlisle", False, 54.8925, -2.9335),
        ("Leeds", False, 53.7950, -1.5470),
        ("Edinburgh Waverley", False, 55.9520, -3.1890),
        ("Glasgow Central", False, 55.8580, -4.2590),
        ("King's Cross", False, 51.5308, -0.1238),
        ("Newcastle", False, 54.9680, -1.6170),
        ("Birmingham New Street", False, 52.4778, -1.8986),
        ("Derby", False, 52.9163, -1.4632),
        ("Bristol Temple Meads", False, 51.4492, -2.5816),
        ("Reading", False, 51.4584, -0.9719),
        ("Leicester", False, 52.6314, -1.1253),
        ("Sheffield", False, 53.3780, -1.4610),
        ("Bounds Green Depot", True, 51.6048, -0.1243),
        ("Crewe Basford Hall", True, 53.1031, -2.4277),
        ("Millerhill Depot", True, 55.9338, -3.0798),
    ]

    locomotive_numbers = {
        "Class 37": [f"37{n:03d}" for n in range(401, 411)],
        "Class 47": [f"47{n:03d}" for n in range(801, 811)],
        "Class 57": [f"57{n:03d}" for n in range(301, 309)],
        "Class 66": [f"66{n:03d}" for n in range(101, 131)],
        "Class 67": [f"67{n:03d}" for n in range(1, 13)],
        "Class 68": [f"68{n:03d}" for n in range(1, 13)],
        "Class 90": [f"90{n:03d}" for n in range(10, 18)],
        "Class 91": [f"91{n:03d}" for n in range(101, 109)],
        "Class 158": [f"158{n:03d}" for n in range(701, 711)],
        "Class 170": [f"170{n:03d}" for n in range(501, 511)],
        "Class 220": [f"220{n:03d}" for n in range(1, 9)],
        "Class 800": [f"800{n:03d}" for n in range(1, 9)],
        "Class 802": [f"802{n:03d}" for n in range(201, 209)],
    }

    builders = ["Brush", "English Electric", "EMD", "Bombardier", "Hitachi", "BREL", "Alstom"]
    wheel_cfg = ["Bo-Bo", "Co-Co", "1A-A1", "2-B+B-2"]
    designers = ["BREL", "Brush Traction", "Hitachi Europe", "Bombardier Derby", "EMD London"]

    locomotives: list[dict] = []
    for class_name, numbers in locomotive_numbers.items():
        for i, number in enumerate(numbers):
            loco_name = f"{class_name} {number}"
            key = f"{normalize(loco_name)}|{normalize(number)}"
            loco = {
                "key": key,
                "locomotiveName": loco_name,
                "recordedNumber": number,
                "buildYear": random.randint(1960, 2020),
                "builtBy": random.choice(builders),
                "powerType": class_type[class_name],
                "wheelConfiguration": random.choice(wheel_cfg),
                "designedBy": random.choice(designers),
                "length": round(random.uniform(60.0, 95.0), 1),
                "weight": round(random.uniform(70.0, 140.0), 1),
                "pressure": round(random.uniform(180.0, 310.0), 1),
                "wantedAt": None,
                "completedAt": None,
                "className": class_name,
            }
            if i % 9 == 0:
                loco["designedBy"] = None
            if i % 11 == 0:
                loco["wheelConfiguration"] = None
            if i % 13 == 0:
                loco["pressure"] = None
            locomotives.append(loco)

    period_start = datetime(2023, 1, 1, 8, 0, 0)
    period_end = datetime(2026, 3, 22, 20, 0, 0)

    wish_candidates = random.sample(locomotives, 26)
    completed_wishes = wish_candidates[:15]
    active_wishes = wish_candidates[15:]

    for loco in completed_wishes:
        wanted = period_start + timedelta(days=random.randint(0, 730), hours=random.randint(0, 12))
        completed = wanted + timedelta(days=random.randint(14, 420), hours=random.randint(0, 8))
        if completed > period_end:
            completed = period_end - timedelta(days=random.randint(0, 20))
        loco["wantedAt"] = iso_utc(wanted)
        loco["completedAt"] = iso_utc(completed)

    for loco in active_wishes:
        wanted = period_start + timedelta(days=random.randint(450, 1160), hours=random.randint(0, 12))
        if wanted > period_end:
            wanted = period_end - timedelta(days=random.randint(2, 40))
        loco["wantedAt"] = iso_utc(wanted)

    # Historical edge-case style number-only wish.
    number_only_number = "66777"
    locomotives.append(
        {
            "key": f"|{normalize(number_only_number)}",
            "locomotiveName": "",
            "recordedNumber": number_only_number,
            "buildYear": None,
            "builtBy": None,
            "powerType": "Diesel-Electric",
            "wheelConfiguration": None,
            "designedBy": None,
            "length": None,
            "weight": None,
            "pressure": None,
            "wantedAt": iso_utc(datetime(2025, 8, 14, 10, 30, 0)),
            "completedAt": None,
            "className": "Class 66",
        }
    )

    major_locations = ["York", "Doncaster", "Peterborough", "Crewe", "Leeds", "King's Cross", "Newcastle"]
    major_weights = [0.17, 0.14, 0.11, 0.12, 0.11, 0.18, 0.17]
    operator_names = [name for name, _ in operators]
    location_lookup = {name: (lat, lon) for name, _, lat, lon in locations}
    frequent_keys = [loco_entry["key"] for loco_entry in random.sample(locomotives, 20)]

    def pick_loco() -> dict:
        if random.random() < 0.48:
            key = random.choice(frequent_keys)
            for entry in locomotives:
                if entry["key"] == key:
                    return entry
        return random.choice(locomotives)

    note_templates = [
        "Seen on service run with smooth acceleration.",
        "Quick platform stop, logged from footbridge.",
        "Railtour movement observed during afternoon peak.",
        "Passing working; brief sighting only.",
        "Stabled briefly before departure.",
        "Double-headed consist observed.",
        "Late running by around 12 minutes.",
        "Strong performance on departure, clear tone.",
    ]

    spots: list[dict[str, str]] = []
    spot_index = 1
    for year in [2023, 2024, 2025, 2026]:
        end_month = 12 if year < 2026 else 3
        for month in range(1, end_month + 1):
            count = random.randint(4, 8)
            _, days_in_month = calendar.monthrange(year, month)
            for _ in range(count):
                loco = pick_loco()
                day = random.randint(1, days_in_month)
                hour = random.randint(6, 22)
                minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
                spotted_at = datetime(year, month, day, hour, minute, 0)
                if spotted_at < period_start or spotted_at > period_end:
                    continue

                if random.random() < 0.7:
                    location = random.choices(major_locations, weights=major_weights, k=1)[0]
                else:
                    location = random.choice([name for name, _, _, _ in locations])

                class_name = loco["className"]
                loco_type = loco["powerType"]
                condition = random.choices(
                    ["Gleaming", "Clean", "Fair", "Dirty", "Filthy beast", "Weathered"],
                    weights=[0.08, 0.34, 0.29, 0.16, 0.05, 0.08],
                    k=1,
                )[0]
                start_station = random.choice(major_locations)
                end_station = random.choice([s for s in major_locations if s != start_station])
                if random.random() < 0.18:
                    start_station = ""
                    end_station = ""

                note = random.choice(note_templates) if random.random() < 0.82 else ""

                tender_first = ""
                if loco_type == "Steam" or random.random() < 0.25:
                    tender_first = random.choice(["true", "false"])

                onboard = random.choice(["true", "false"]) if random.random() < 0.62 else ""
                ecs = random.choice(["true", "false"]) if random.random() < 0.37 else ""
                accompanied = random.choice(["true", "false"]) if random.random() < 0.28 else ""

                carriage_count = ""
                if random.random() < 0.67:
                    if class_name in {"Class 66", "Class 67", "Class 68", "Class 57", "Class 47"}:
                        carriage_count = str(random.randint(8, 28))
                    else:
                        carriage_count = str(random.randint(3, 10))

                lat, lon = location_lookup[location]
                latitude = round(lat + random.uniform(-0.009, 0.009), 6)
                longitude = round(lon + random.uniform(-0.009, 0.009), 6)
                accuracy = round(random.uniform(4.2, 38.7), 1)
                captured_utc = spotted_at - timedelta(minutes=random.randint(1, 70))

                if random.random() < 0.08:
                    latitude_field, longitude_field, accuracy_field, captured_field = "", "", "", ""
                else:
                    latitude_field = str(latitude)
                    longitude_field = str(longitude)
                    accuracy_field = str(accuracy)
                    captured_field = iso_utc(captured_utc)

                photo_count = random.choices([0, 1, 2, 3], weights=[0.36, 0.38, 0.19, 0.07], k=1)[0]
                photo_paths = []
                for i in range(photo_count):
                    base_name = f"IMG_{spotted_at.strftime('%Y%m%d_%H%M%S')}_{i + 1}.jpg"
                    photo_paths.append(f"photos/spot-{spot_index:04d}_{i}_{base_name}")

                spots.append(
                    {
                        "id": f"spot-{spot_index:04d}-{uuid.uuid4().hex[:8]}",
                        "locoNumber": loco["recordedNumber"],
                        "locoName": loco["locomotiveName"],
                        "class": class_name,
                        "locoType": loco_type,
                        "operator": random.choice(operator_names),
                        "location": location,
                        "startStation": start_station,
                        "endStation": end_station,
                        "notes": note,
                        "condition": condition,
                        "date": iso_local(spotted_at),
                        "tenderFirst": tender_first,
                        "onboard": onboard,
                        "ecs": ecs,
                        "accompanied": accompanied,
                        "carriageCount": carriage_count,
                        "latitude": latitude_field,
                        "longitude": longitude_field,
                        "accuracyMeters": accuracy_field,
                        "locationCapturedAtUtc": captured_field,
                        "photoCount": str(photo_count),
                        "photoPaths": ";".join(photo_paths),
                    }
                )
                spot_index += 1

    spots.sort(key=lambda row: row["date"])

    spots_header = [
        "id",
        "locoNumber",
        "locoName",
        "class",
        "locoType",
        "operator",
        "location",
        "startStation",
        "endStation",
        "notes",
        "condition",
        "date",
        "tenderFirst",
        "onboard",
        "ecs",
        "accompanied",
        "carriageCount",
        "latitude",
        "longitude",
        "accuracyMeters",
        "locationCapturedAtUtc",
        "photoCount",
        "photoPaths",
    ]

    with (output_dir / "spots.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=spots_header)
        writer.writeheader()
        writer.writerows(spots)

    classes_rows = [{"key": normalize(c), "className": c} for c in classes]
    types_rows = [{"key": normalize(t), "name": t} for t in types]
    conditions_rows = [{"key": normalize(c), "name": c} for c in conditions]
    locations_rows = [
        {"key": normalize(name), "name": name, "isUserAdded": str(is_user).lower()}
        for name, is_user, _, _ in locations
    ]
    operators_rows = [
        {"key": normalize(name), "name": name, "isUserAdded": str(is_user).lower()}
        for name, is_user in operators
    ]

    loco_rows = []
    for loco in locomotives:
        loco_rows.append(
            {
                "key": loco["key"],
                "locomotiveName": loco["locomotiveName"],
                "recordedNumber": loco["recordedNumber"],
                "buildYear": "" if loco["buildYear"] is None else str(loco["buildYear"]),
                "builtBy": "" if loco["builtBy"] is None else loco["builtBy"],
                "powerType": "" if loco["powerType"] is None else loco["powerType"],
                "wheelConfiguration": "" if loco["wheelConfiguration"] is None else loco["wheelConfiguration"],
                "designedBy": "" if loco["designedBy"] is None else loco["designedBy"],
                "length": "" if loco["length"] is None else str(loco["length"]),
                "weight": "" if loco["weight"] is None else str(loco["weight"]),
                "pressure": "" if loco["pressure"] is None else str(loco["pressure"]),
                "wantedAt": "" if loco["wantedAt"] is None else loco["wantedAt"],
                "completedAt": "" if loco["completedAt"] is None else loco["completedAt"],
            }
        )

    csv_specs: list[tuple[str, list[str], list[dict[str, str]]]] = [
        ("classes.csv", ["key", "className"], classes_rows),
        ("types.csv", ["key", "name"], types_rows),
        ("conditions.csv", ["key", "name"], conditions_rows),
        ("locations.csv", ["key", "name", "isUserAdded"], locations_rows),
        ("operators.csv", ["key", "name", "isUserAdded"], operators_rows),
        (
            "locomotive_details.csv",
            [
                "key",
                "locomotiveName",
                "recordedNumber",
                "buildYear",
                "builtBy",
                "powerType",
                "wheelConfiguration",
                "designedBy",
                "length",
                "weight",
                "pressure",
                "wantedAt",
                "completedAt",
            ],
            loco_rows,
        ),
    ]

    for file_name, header, rows in csv_specs:
        with (output_dir / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    # JSON payloads matching reference files in FULL backup.
    (ref_dir / "classes.json").write_text(
        json.dumps([{"key": row["key"], "className": row["className"]} for row in classes_rows], indent=2),
        encoding="utf-8",
    )
    (ref_dir / "types.json").write_text(
        json.dumps([{"key": row["key"], "name": row["name"]} for row in types_rows], indent=2),
        encoding="utf-8",
    )
    (ref_dir / "conditions.json").write_text(
        json.dumps([{"key": row["key"], "name": row["name"]} for row in conditions_rows], indent=2),
        encoding="utf-8",
    )
    (ref_dir / "locations.json").write_text(
        json.dumps(
            [{"key": normalize(name), "name": name, "isUserAdded": is_user} for name, is_user, _, _ in locations],
            indent=2,
        ),
        encoding="utf-8",
    )
    (ref_dir / "operators.json").write_text(
        json.dumps([{"key": normalize(name), "name": name, "isUserAdded": is_user} for name, is_user in operators], indent=2),
        encoding="utf-8",
    )
    (ref_dir / "locomotive_details.json").write_text(
        json.dumps(
            [
                {
                    "key": loco["key"],
                    "locomotiveName": loco["locomotiveName"],
                    "recordedNumber": loco["recordedNumber"],
                    "buildYear": loco["buildYear"],
                    "builtBy": loco["builtBy"],
                    "powerType": loco["powerType"],
                    "wheelConfiguration": loco["wheelConfiguration"],
                    "designedBy": loco["designedBy"],
                    "length": loco["length"],
                    "weight": loco["weight"],
                    "pressure": loco["pressure"],
                    "wantedAt": loco["wantedAt"],
                    "completedAt": loco["completedAt"],
                }
                for loco in locomotives
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "spots.csv": len(spots),
        "classes.csv": len(classes_rows),
        "types.csv": len(types_rows),
        "conditions.csv": len(conditions_rows),
        "locations.csv": len(locations_rows),
        "operators.csv": len(operators_rows),
        "locomotive_details.csv": len(loco_rows),
    }


class HeadcodeDummyGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Headcode Dummy Export Generator")
        self.root.geometry("860x620")
        self.root.minsize(760, 520)

        self.output_dir_var = tk.StringVar(value="dummy_data/headcode_full_export_3y")
        self.seed_var = tk.StringVar(value="20260322")
        self.status_var = tk.StringVar(value="Choose output options and click Generate.")

        self._queue: queue.Queue[tuple[str, tuple]] = queue.Queue()
        self._is_running = False
        self._build_ui()
        self.root.after(100, self._poll_queue)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        options = ttk.LabelFrame(container, text="Generation Options", padding=12)
        options.pack(fill=tk.X)

        ttk.Label(options, text="Output folder").grid(row=0, column=0, sticky="w")
        self.output_entry = ttk.Entry(options, textvariable=self.output_dir_var, width=78)
        self.output_entry.grid(row=1, column=0, padx=(0, 8), pady=(4, 10), sticky="ew")
        self.output_button = ttk.Button(options, text="Browse...", command=self._choose_output_dir)
        self.output_button.grid(row=1, column=1, pady=(4, 10), sticky="ew")

        ttk.Label(options, text="Random seed").grid(row=2, column=0, sticky="w")
        self.seed_entry = ttk.Entry(options, textvariable=self.seed_var, width=22)
        self.seed_entry.grid(row=3, column=0, pady=(4, 10), sticky="w")
        options.columnconfigure(0, weight=1)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(10, 8))
        self.generate_button = ttk.Button(actions, text="Generate Dummy Export", command=self._start_generation)
        self.generate_button.pack(side=tk.LEFT)
        self.clear_button = ttk.Button(actions, text="Clear Log", command=self._clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=(8, 0))

        progress = ttk.LabelFrame(container, text="Progress", padding=12)
        progress.pack(fill=tk.X)
        self.progress = ttk.Progressbar(progress, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(progress, textvariable=self.status_var, anchor="w").pack(fill=tk.X)

        log_frame = ttk.LabelFrame(container, text="Activity Log", padding=12)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, height=16, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_dir_var.set(path)

    def _log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _set_running_state(self, running: bool) -> None:
        self._is_running = running
        control_state = tk.DISABLED if running else tk.NORMAL
        self.generate_button.configure(state=control_state)
        self.output_button.configure(state=control_state)
        self.output_entry.configure(state=control_state)
        self.seed_entry.configure(state=control_state)
        self.clear_button.configure(state=control_state)
        if running:
            self.progress.start(10)
        else:
            self.progress.stop()

    def _start_generation(self) -> None:
        if self._is_running:
            return

        output_dir_raw = self.output_dir_var.get().strip()
        if not output_dir_raw:
            messagebox.showerror("Missing Output Folder", "Enter or choose an output folder.")
            return

        seed_text = self.seed_var.get().strip()
        try:
            seed = int(seed_text)
        except ValueError:
            messagebox.showerror("Invalid Seed", "Seed must be a whole number.")
            return

        output_dir = Path(output_dir_raw)
        output_dir.mkdir(parents=True, exist_ok=True)

        self._set_running_state(True)
        self.status_var.set("Generating dummy export files...")
        self._log("=" * 72)
        self._log(f"Output folder: {output_dir.resolve()}")
        self._log(f"Seed: {seed}")

        threading.Thread(
            target=self._worker_generate,
            args=(output_dir, seed),
            daemon=True,
        ).start()

    def _worker_generate(self, output_dir: Path, seed: int) -> None:
        try:
            counts = build_dataset(output_dir=output_dir, seed=seed)
            self._queue.put(("done_ok", (output_dir, counts)))
        except Exception as exc:
            self._queue.put(("done_error", (str(exc),)))

    def _poll_queue(self) -> None:
        try:
            while True:
                event, payload = self._queue.get_nowait()

                if event == "done_ok":
                    output_dir, counts = payload
                    self._set_running_state(False)
                    self.status_var.set("Generation complete.")
                    self._log("Generation complete:")
                    for name, count in counts.items():
                        self._log(f"- {name}: {count} rows")
                    self._log(f"Files written to: {output_dir.resolve()}")
                    messagebox.showinfo(
                        "Done",
                        f"Dummy Headcode export generated successfully.\n\nOutput:\n{output_dir.resolve()}",
                    )
                elif event == "done_error":
                    (message,) = payload
                    self._set_running_state(False)
                    self.status_var.set("Generation failed. Check log.")
                    self._log(f"ERROR: {message}")
                    messagebox.showerror("Generation Failed", message)
        except queue.Empty:
            pass

        self.root.after(100, self._poll_queue)


def launch_gui() -> None:
    if tk is None:
        raise RuntimeError(
            "Tkinter is not available in this Python environment. "
            "Install Python with Tk support or run the CLI mode."
        )
    root = tk.Tk()
    HeadcodeDummyGui(root)
    root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a dummy Headcode FULL export dataset (CSV + reference JSON)."
    )
    parser.add_argument(
        "--output-dir",
        default="dummy_data/headcode_full_export_3y",
        help="Directory to write generated files into.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260322,
        help="Random seed for deterministic output.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch desktop GUI mode for end users.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.gui:
        launch_gui()
        return

    output_dir = Path(args.output_dir)
    counts = build_dataset(output_dir=output_dir, seed=args.seed)

    print(f"Generated files in {output_dir}")
    for name, count in counts.items():
        print(f"- {name} rows: {count}")


if __name__ == "__main__":
    main()
