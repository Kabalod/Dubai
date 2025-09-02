import json  # JSON operations
import logging  # Logging
import tempfile  # Temp directory
import zipfile  # ZIP extraction
from pathlib import Path  # File paths

import pandas as pd  # DataFrame support
from rapidfuzz import fuzz  # Fuzzy matching
from rapidfuzz import process  # Fuzzy matching
from realty.main.management.utils import download_dubai_pulse_csv
from realty.main.management.utils import safe_str_value

logger = logging.getLogger(__name__)


def get_projects_file(projects_zip_file: str) -> Path:
    projects_file = download_dubai_pulse_csv(
        site_url="https://www.dubaipulse.gov.ae/data/dld-registration/dld_projects-open",
        file_type="projects",
    )
    logger.info("Loading projects CSV")
    projects_df = pd.read_csv(projects_file)
    projects_df.columns = [c.lower() for c in projects_df.columns]
    projects_df["project_name_norm"] = (
        projects_df["project_name"].astype(str).apply(normalize_str)
    )
    all_project_names = projects_df["project_name_norm"].dropna().unique().tolist()

    zf = zipfile.ZipFile(projects_zip_file)
    with tempfile.TemporaryDirectory() as tempdir:
        logger.info("Extracting JSONs from ZIP")
        zf.extractall(tempdir)
        result_rows = []

        logger.info("Processing JSON projects")
        for file in Path(tempdir).glob("**/*.json"):
            logger.info(f"Processing {file}")
            data = json.loads(file.read_text())
            proj_data = data.get("response", {}).get("project", {})
            if not proj_data:
                continue

            title = proj_data.get("title", {})
            project_number = title.get("number", "")
            json_project_name = normalize_str(
                title.get("name", {}).get("englishName", "")
            )
            street_en = (
                proj_data.get("location", {}).get("street", {}).get("englishName", "")
            )
            # Split street into (project_name_from_street, area)
            project_name_from_street, area_name = extract_area_from_street(street_en)
            if not json_project_name:
                json_project_name = project_name_from_street
            total_units = title.get("totalUnits", 0)
            room_types_str = extract_room_types(proj_data.get("functions", []))

            buildings_data = proj_data.get("buidlings", [])
            building_count = len(buildings_data)

            if building_count > 0:
                for building in buildings_data:
                    json_building_name = safe_str_value(
                        building.get("name", {}).get("englishName", "")
                    )
                    if not json_building_name:
                        json_building_name = json_project_name
                    building_floor = building.get("floorCount", 0)
                    row_dict = {
                        "json_project_number": project_number,
                        "json_project_name": json_project_name,
                        "json_building_name": json_building_name,
                        "area": area_name,
                        "total_units": total_units,
                        "room_types": room_types_str,
                        "floors": building_floor,
                        "building_count": building_count,
                        "match_method": "",
                        "matched_project_id": "",
                        "matched_project_number": "",
                        "matched_project_name": "",
                    }
                    result_rows.append(row_dict)
            else:
                row_dict = {
                    "json_project_number": project_number,
                    "json_project_name": json_project_name,
                    "json_building_name": json_project_name,
                    "area": area_name,
                    "total_units": total_units,
                    "room_types": room_types_str,
                    "floors": 0,
                    "building_count": 0,
                    "match_method": "",
                    "matched_project_id": "",
                    "matched_project_number": "",
                    "matched_project_name": "",
                }
                result_rows.append(row_dict)

    final_df = pd.DataFrame(result_rows)
    filename = projects_file.parent / f"{projects_file.stem}_matched_fuzzy.csv"
    final_df.to_csv(filename, index=False)
    logger.info(f"Saved {filename}")
    return filename


def normalize_str(s):
    if not s:
        return ""
    return s.strip().lower()


def extract_area_from_street(street_en: str) -> tuple:
    if not street_en:
        return ("", "")
    parts = street_en.split(",")
    if len(parts) > 1:
        return (parts[0].strip(), parts[-1].strip())
    else:
        return (street_en.strip(), street_en.strip())


def extract_room_types(functions: list) -> str:
    if not functions:
        return ""
    room_strings = []
    for func in functions:
        rooms = func.get("rooms", [])
        for r in rooms:
            en_name = r["name"].get("englishName", "")
            val = r.get("value", "")
            if en_name and val:
                room_strings.append(f"{en_name}({val})")
    return "; ".join(room_strings)


def sum_of_floors(buildings_data: list) -> int:
    if not buildings_data:
        return 0
    total = 0
    for b in buildings_data:
        floor_count = b.get("floorCount", 0)
        if floor_count is not None:
            total += floor_count
    return total


def fuzzy_match_project_name(name_json: str, all_names: list, threshold=80):
    if not name_json:
        return None, 0
    result = process.extractOne(name_json, all_names, scorer=fuzz.WRatio)
    if result is None:
        return None, 0
    best_match, best_score, _ = result
    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score
