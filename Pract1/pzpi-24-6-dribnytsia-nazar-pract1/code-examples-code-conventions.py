"""Приклади оформлення коду мовою Python за рекомендаціями PEP 8.

Файл супроводжує звіт до практичного завдання № 1 з дисципліни
«Аналіз та рефакторинг коду програмного забезпечення». Приклади
взято з предметної області проєкту «Оберіг» (охорона житла).

Запуск: python code-examples-code-conventions.py
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Іменування: константи — UPPER_CASE на рівні модуля
# ---------------------------------------------------------------------------
DUPLICATE_WINDOW_SEC = 5
CONFIRM_WINDOW_SEC = 60
ALARM_THRESHOLD = 0.4

# Ваги датчиків (словник замість «магічних чисел» у коді)
SENSOR_WEIGHTS = {"reed": 0.5, "pir": 0.4, "tamper": 1.0}


# ---------------------------------------------------------------------------
# 2. Іменування: винятки завершуються словом Error, класи — PascalCase
# ---------------------------------------------------------------------------
class UnknownSensorError(Exception):
    """Тип датчика відсутній у таблиці ваг."""


@dataclass
class SensorEvent:
    """Подія, отримана від датчика IoT-вузла.

    Attributes:
        node_id: ідентифікатор вузла.
        sensor_type: тип датчика (reed, pir, tamper).
        timestamp_sec: час події в секундах (UTC).
        seq: порядковий номер події вузла.
    """

    node_id: str
    sensor_type: str
    timestamp_sec: float
    seq: int


# ---------------------------------------------------------------------------
# 3. Функції: snake_case, дієслова в назвах, докстринги та анотації типів
# ---------------------------------------------------------------------------
def is_duplicate(first: SensorEvent, second: SensorEvent) -> bool:
    """Перевіряє, чи є друга подія дублікатом першої.

    Args:
        first: раніше отримана подія.
        second: щойно отримана подія.

    Returns:
        True, якщо події з одного вузла й датчика мають однаковий
        порядковий номер або надійшли в межах вікна дедуплікації.
    """
    same_source = (
        first.node_id == second.node_id
        and first.sensor_type == second.sensor_type
    )
    if not same_source:
        return False
    close_in_time = (
        abs(first.timestamp_sec - second.timestamp_sec) < DUPLICATE_WINDOW_SEC
    )
    return close_in_time or first.seq == second.seq


def get_sensor_weight(sensor_type: str) -> float:
    """Повертає вагу датчика або піднімає UnknownSensorError."""
    try:
        return SENSOR_WEIGHTS[sensor_type]
    except KeyError as error:
        # Перехоплюємо конкретний виняток і додаємо зрозуміле пояснення
        raise UnknownSensorError(f"Невідомий датчик: {sensor_type}") from error


# ---------------------------------------------------------------------------
# 4. Принцип єдиної відповідальності: кожна функція виконує одну дію
# ---------------------------------------------------------------------------
def remove_duplicates(events: list[SensorEvent]) -> list[SensorEvent]:
    """Повертає список подій без дублікатів, зберігаючи порядок."""
    unique: list[SensorEvent] = []
    for event in events:
        if not any(is_duplicate(known, event) for known in unique):
            unique.append(event)
    return unique


def calculate_confidence(events: list[SensorEvent]) -> float:
    """Обчислює індекс достовірності як суму ваг різних датчиків."""
    distinct_types = {event.sensor_type for event in events}
    return sum(get_sensor_weight(kind) for kind in distinct_types)


def classify_alarm(confidence: float) -> Optional[str]:
    """Визначає рівень тривоги за індексом достовірності."""
    if confidence >= 0.9:
        return "confirmed"
    if confidence >= ALARM_THRESHOLD:
        return "alarm"
    return None


def process_events(events: list[SensorEvent]) -> Optional[str]:
    """Обробляє пакет подій: дедуплікація, оцінка, класифікація."""
    unique_events = remove_duplicates(events)
    confidence = calculate_confidence(unique_events)
    return classify_alarm(confidence)


# ---------------------------------------------------------------------------
# 5. Ідіоматичний стиль Python
# ---------------------------------------------------------------------------
def build_summary(events: list[SensorEvent]) -> list[str]:
    """Формує текстовий опис подій (спискове включення, enumerate, f-рядок)."""
    return [
        f"{number}. {event.node_id}: {event.sensor_type}"
        for number, event in enumerate(events, start=1)
    ]


def read_log_lines(path: str) -> list[str]:
    """Читає рядки журналу; файл гарантовано закривається (with)."""
    try:
        with open(path, encoding="utf-8") as log_file:
            return [line.rstrip("\n") for line in log_file]
    except FileNotFoundError:
        logger.warning("Файл журналу %s не знайдено", path)
        return []


def main() -> None:
    """Демонстрація роботи прикладів."""
    events = [
        SensorEvent("node-1", "reed", 100.0, 1),
        SensorEvent("node-1", "reed", 102.0, 2),  # дублікат (менше 5 с)
        SensorEvent("node-1", "pir", 110.0, 3),
    ]
    for line in build_summary(remove_duplicates(events)):
        print(line)
    print("Рівень тривоги:", process_events(events))

    try:
        get_sensor_weight("smoke")
    except UnknownSensorError as error:
        print("Помилка:", error)

    print(read_log_lines("missing.log"))


if __name__ == "__main__":
    main()
