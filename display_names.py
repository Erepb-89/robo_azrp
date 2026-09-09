"""
Читаемые названия для точек, траекторий и действий манипулятора.
Используется в UI для отображения вместо внутренних технических имён.
"""

POINT_NAMES: dict[str, str] = {
    "pHomePosition":             "Домашняя позиция",
    # Вертолёты
    "pHelicopterModule":         "Модуль вертолётов",
    "pHelicopter1":              "Вертолёт 1",
    "pHelicopter1Payload":       "Вертолёт 1: Полезная нагрузка",
    "pHelicopter2":              "Вертолёт 2",
    "pHelicopter2Payload":       "Вертолёт 2: Полезная нагрузка",
    # ВТОЛ1
    "pVTOLModule":               "Модуль ВТОЛ",
    "pVTOL1":                    "ВТОЛ 1",
    "pVTOL1Payload":             "ВТОЛ 1: Полезная нагрузка",
    "pVTOL1Battery":             "ВТОЛ 1: батарея",
    "pVTOL2":                    "ВТОЛ 2",
    # Полезная нагрузка
    "pPayload":                  "Хранилище полезной нагрузки",
    "pPayload1":                 "Полезная нагрузка — место 1",
    "pPayload2":                 "Полезная нагрузка — место 2",
    # Захваты
    "pGrippers":                 "Хранилище захватов",
    "pGrippers1":                "Захват 1",
    "pGrippers2":                "Захват 2",
    # Зарядная станция
    "pCharger":                  "Зарядная станция",
    "pCharger1":                 "Зарядное место 1",
    "pCharger2":                 "Зарядное место 2",
    # ВТОЛ2 — батарея 1
    "pVTOL2Battery":             "ВТОЛ2: батарея",
    "pVTOL2BatteryOut":          "ВТОЛ2: батарея — вынос",
    "pVTOL2BatteryIn":           "ВТОЛ2: батарея — установка",
    "pVTOL2BatteryPreCharge":    "ВТОЛ2: батарея — подача к зарядке",
    "pVTOL2BatteryUp":           "ВТОЛ2: батарея — подъём",
    "pVTOL2BatteryOnCharge":     "ВТОЛ2: батарея — на зарядке",
    # ВТОЛ2 — батарея 2
    "pVTOL2Battery2":            "ВТОЛ2: батарея 2",
    "pVTOL2Battery2Out":         "ВТОЛ2: батарея 2 — вынос",
    "pVTOL2Battery2OutPreMove":  "ВТОЛ2: батарея 2 — подготовка выноса",
    "pVTOL2Battery2OutMove":     "ВТОЛ2: батарея 2 — вынос (движение)",
    "pVTOL2Battery2Up":          "ВТОЛ2: батарея 2 — подъём",
    "pVTOL2Battery2PreStation":  "ВТОЛ2: батарея 2 — к станции",
    "pVTOL2Battery2PreCharge":   "ВТОЛ2: батарея 2 — подача к зарядке",
    "pVTOL2Battery2Charge":      "ВТОЛ2: батарея 2 — зарядка",
    "pVTOL2Battery2AfterCharge": "ВТОЛ2: батарея 2 — после зарядки",
    "pVTOL2Battery2OutMove2":    "ВТОЛ2: батарея 2 — вынос 2",
    "pVTOL2Battery2PreMove2":    "ВТОЛ2: батарея 2 — подготовка 2",
    "pVTOL2Battery2PreBatt":     "ВТОЛ2: батарея 2 — к отсеку",
    "pVTOL2Battery2Batt2":       "ВТОЛ2: батарея 2 — отсек 2",
    "pVTOL2Battery2BatteryIn":   "ВТОЛ2: батарея 2 — установка",
    "pVTOL2Battery2PreStop":     "ВТОЛ2: батарея 2 — подготовка стопа",
    "pVTOL2Battery2Stop":        "ВТОЛ2: батарея 2 — стоп",
}

ACTION_NAMES: dict[str, str] = {
    "aVTOL2_To_VTOL2Battery":  "VTOL2: взять батарею",
    "aVTOL2Battery_To_VTOL2":  "VTOL2: достать батарею",
}


def traj_display_name(key: str) -> str:
    """
    Преобразует внутреннее имя траектории в читаемое.
    Пример: 'tHomePosition_To_HelicopterModule' → 'Домашняя позиция → Модуль вертолётов'
    Для неизвестных имён возвращает исходную строку.
    """
    if not key.startswith('t'):
        return key
    body = key[1:]
    if '_To_' not in body:
        return key
    src_raw, dst_raw = body.split('_To_', 1)
    src = POINT_NAMES.get(f"p{src_raw}", src_raw)
    dst = POINT_NAMES.get(f"p{dst_raw}", dst_raw)
    return f"{src} → {dst}"
