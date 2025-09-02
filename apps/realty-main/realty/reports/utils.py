# /utils.py
import json
from typing import Tuple, Optional


ROOM_MAPPING = {
    "studio": ["Studio"],
    "1br": ["1 B/R"],
    "2br": ["2 B/R"],
    "3br": ["3 B/R"],
    "4br": ["4 B/R"],
}


def _bedrooms_to_int(key: str | None) -> int | None:
    """
    'studio' → 0, '1br' → 1, '2br' → 2 … ;  None / мусор → None
    """
    if not key:
        return None
    key = key.lower()
    if key == "studio":
        return 0
    for ch in key:
        if ch.isdigit():
            return int(ch)
    return None


def get_room_int_and_units(
    pf_building, bedrooms: str
) -> Tuple[Optional[int], Optional[int]]:
    """
    Возвращает кортеж (room_int, room_units):

    * `room_int`  – целое число комнат (0 для studio, 1 для 1br …);
    * `room_units` – сколько юнитов такой комнатности указано в
      JSON‑поле `pf_building.dld_building.arabic_name`
      (ключ `"rooms_count": {"1 B/R": 362, …}`).

    Если данные недоступны → обоих элементов может быть `None`.
    """
    room_int = _bedrooms_to_int(bedrooms)
    if room_int is None:
        return None, None
    # 2) читаем JSON с количеством юнитов, но только если есть ключи
    room_units = None
    try:
        raw_json = getattr(pf_building.dld_building, "arabic_name", "{}") or "{}"
        data = json.loads(raw_json)
        rooms_map = data.get("rooms_count")

        # если rooms_map — непустой dict, ищем пересечение ключей

        if isinstance(rooms_map, dict) and rooms_map:
            raw_keys = ROOM_MAPPING.get(bedrooms.lower(), [bedrooms])
            present = [k for k in raw_keys if k in rooms_map]
            if present:
                room_units = sum(rooms_map.get(k, 0) for k in present)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
        pass

    return room_int, room_units


def get_room_int_and_units_2(
    pf_building, bedrooms: str
) -> Tuple[Optional[int], Optional[int]]:
    room_int = _bedrooms_to_int(bedrooms)
    if room_int is None:
        return None, None

    # --- НОВОЕ: нормализуем текстовый ключ ----------------------------
    key_norm = (bedrooms or "").lower().strip()
    if key_norm.isdigit():  # '1' → '1br'
        key_norm = f"{key_norm}br"
    elif key_norm.endswith("+"):  # '5+' → '5br' (условно)
        key_norm = f"{key_norm.rstrip('+')}br"

    # -------------------------------------------------------------------
    room_units = None
    try:
        raw_json = getattr(pf_building.dld_building, "arabic_name", "{}") or "{}"
        data = json.loads(raw_json)
        rooms_map = data.get("rooms_count")

        if isinstance(rooms_map, dict) and rooms_map:
            raw_keys = ROOM_MAPPING.get(key_norm, [key_norm])
            present = [k for k in raw_keys if k in rooms_map]
            if present:
                room_units = sum(rooms_map.get(k, 0) for k in present)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
        pass

    return room_int, room_units
