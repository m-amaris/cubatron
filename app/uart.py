from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import re
import unicodedata

from app.config import (
    UART_ENABLED,
    UART_DRY_RUN,
    UART_PORT,
    UART_BAUDRATE,
    UART_TIMEOUT,
    UART_WRITE_TIMEOUT,
    UART_LOG_PATH,
)

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    serial = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_liquid_name(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"\s+", " ", ascii_value)
    return ascii_value.strip().lower()


def frame_command(payload: str) -> str:
    cleaned = str(payload or "").strip()
    if not cleaned:
        raise ValueError("UART command is empty")
    if cleaned.startswith("|") and cleaned.endswith("|"):
        return cleaned
    cleaned = cleaned.strip("|")
    return f"|{cleaned}|"


def build_command(command: str, *args: object) -> str:
    parts = [str(command).strip().upper()]
    for arg in args:
        parts.append(str(arg))
    return frame_command(";".join(parts))


def build_make_command(slot_ml: list[int]) -> str:
    if len(slot_ml) != 4:
        raise ValueError("MAKE needs 4 slot values")
    safe = [max(0, int(value)) for value in slot_ml]
    return build_command("MAKE", *safe)


def build_clean_command(slot: int | None = None) -> str:
    if slot is None:
        return build_command("CLEAN")
    return build_command("CLEAN", int(slot))


def build_stop_command() -> str:
    return build_command("STOP")


def build_status_command() -> str:
    return build_command("STATUS")


def build_temp_command(target_c: float) -> str:
    safe = float(target_c)
    return build_command("TEMP", format(safe, "g"))


def map_liquids_to_slots(
    tanks: list[dict],
    breakdown: list[dict],
) -> tuple[list[int], list[str], dict[str, int]]:
    slot_values = {1: 0, 2: 0, 3: 0, 4: 0}
    name_to_slot: dict[str, int] = {}

    for tank in tanks:
        if tank.get("enabled") is False:
            continue
        try:
            slot = int(tank.get("slot") or 0)
        except Exception:
            continue
        if slot not in slot_values:
            continue

        for key in ("name", "content"):
            normalized = normalize_liquid_name(tank.get(key) or "")
            if normalized and normalized not in name_to_slot:
                name_to_slot[normalized] = slot

    missing: set[str] = set()
    resolved: dict[str, int] = {}
    for item in breakdown:
        liquid_raw = str(item.get("liquid") or "").strip()
        if not liquid_raw:
            continue
        normalized = normalize_liquid_name(liquid_raw)
        try:
            ml_value = int(round(float(item.get("ml") or 0)))
        except Exception:
            ml_value = 0
        if ml_value <= 0:
            continue
        slot = name_to_slot.get(normalized)
        if not slot:
            missing.add(liquid_raw)
            continue
        slot_values[slot] += ml_value
        resolved[liquid_raw] = slot

    return [slot_values[i] for i in range(1, 5)], sorted(missing), resolved


class UartManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._serial = None
        self._last_write: dict | None = None

    def _open(self):
        if serial is None:
            raise RuntimeError("pyserial no esta disponible")
        if not UART_PORT:
            raise RuntimeError("UART_PORT no configurado")
        return serial.Serial(
            port=UART_PORT,
            baudrate=UART_BAUDRATE,
            timeout=UART_TIMEOUT,
            write_timeout=UART_WRITE_TIMEOUT,
        )

    def _get_serial(self):
        if self._serial is not None:
            try:
                if getattr(self._serial, "is_open", False):
                    return self._serial
            except Exception:
                self._serial = None
        self._serial = self._open()
        return self._serial

    def _append_log(self, payload: dict) -> None:
        if not UART_LOG_PATH:
            return
        path = Path(UART_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = f"{payload.get('timestamp')} | {payload.get('status')} | {payload.get('command')}"
        error = payload.get("error")
        if error:
            line += f" | error={error}"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def send(self, command: str) -> dict:
        framed = frame_command(command)
        payload = {
            "timestamp": _now_iso(),
            "command": framed,
            "port": UART_PORT,
            "baudrate": UART_BAUDRATE,
            "status": "pending",
        }

        if not UART_ENABLED:
            payload.update({"ok": True, "status": "skipped", "skipped": True, "reason": "uart_disabled"})
            self._last_write = payload
            self._append_log(payload)
            return payload

        if UART_DRY_RUN:
            payload.update({
                "ok": True,
                "status": "dry_run",
                "dry_run": True,
                "bytes_written": len(framed.encode("ascii")),
            })
            self._last_write = payload
            self._append_log(payload)
            return payload

        with self._lock:
            try:
                serial_conn = self._get_serial()
                encoded = framed.encode("ascii")
                bytes_written = serial_conn.write(encoded)
                try:
                    serial_conn.flush()
                except Exception:
                    pass
                payload.update({"ok": True, "status": "written", "bytes_written": bytes_written})
            except Exception as exc:
                payload.update({"ok": False, "status": "error", "error": str(exc)})

        self._last_write = payload
        self._append_log(payload)
        return payload

    def last_write(self) -> dict | None:
        return self._last_write


_UART_MANAGER = UartManager()


def send_uart_command(command: str) -> dict:
    return _UART_MANAGER.send(command)


def get_last_uart_write() -> dict | None:
    return _UART_MANAGER.last_write()
