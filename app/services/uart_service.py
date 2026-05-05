import asyncio
import os
import time
from typing import Dict, Optional
from app.config import SessionLocal
from app.models.models import History, User


class MachineBusyError(Exception):
    pass


class InsufficientDepositError(Exception):
    pass


class UARTService:
    """
    UART service that talks to the hardware via pyserial or simulates behavior when dry-run.
    It exposes async methods and manages an internal lock/state.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.state = 'IDLE'
        self.lock = asyncio.Lock()
        # levels for 4 deposits (ml)
        self.levels = [1000, 1000, 1000, 1000]
        self.temperature = 22.0
        self._task: Optional[asyncio.Task] = None

    async def get_status(self) -> Dict:
        # Build STATUS command and parse response to obey protocol
        resp = await self._send_command('STATUS')
        parsed = self._parse_status_response(resp)
        return parsed

    def _log_uart(self, direction: str, data: str):
        """Log UART communication to data/uart.log"""
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uart.log')
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(log_path, 'a') as f:
                f.write(f"[{ts}] {direction}: {data}\n")
        except Exception:
            pass

    async def _send_command(self, cmd: str) -> str:
        """Send a raw command to the hardware or simulate it in dry-run.
        Recognized commands: MAKE, CLEAN, STOP, TEMP, STATUS
        """
        self._log_uart('TX', cmd)

        if self.dry_run:
            resp = self._simulate_response(cmd)
            self._log_uart('RX', resp)
            return resp
        else:
            try:
                import serial
                port = os.getenv('CUBATRON_UART_PORT', '/dev/serial0')
                baudrate = int(os.getenv('CUBATRON_UART_BAUDRATE', '115200'))
                ser = serial.Serial(port, baudrate, timeout=2)
                # Protocol uses pipe-delimited frames without newlines
                ser.write(cmd.encode())
                # Read until closing pipe
                resp = ''
                while True:
                    ch = ser.read(1)
                    if not ch:
                        break
                    resp += ch.decode(errors='replace')
                    if ch == b'|' and resp.startswith('|'):
                        break
                ser.close()
                resp = resp.strip()
                self._log_uart('RX', resp)
                return resp
            except Exception as e:
                self._log_uart('ERROR', str(e))
                return '|ERROR|'

    def _simulate_response(self, cmd: str) -> str:
        """Generate simulated responses for dry-run mode."""
        if cmd.startswith('MAKE'):
            return '|ACK|'
        if cmd == 'CLEAN':
            return '|ACK|'
        if cmd == 'STOP':
            return '|ACK|'
        if cmd.startswith('TEMP'):
            return '|ACK|'
        if cmd == 'STATUS':
            return f"|INFO;{self.state};{self.levels[0]};{self.levels[1]};{self.levels[2]};{self.levels[3]};{round(self.temperature,1)}|"
        return '|OK|'

    def _parse_status_response(self, resp: str) -> Dict:
        # Expecting format: |INFO;estado;nivel1;nivel2;nivel3;nivel4;temperatura|
        try:
            if not resp or 'INFO' not in resp:
                return {'state': self.state, 'levels': list(self.levels), 'temperature': self.temperature, 'message': resp}
            s = resp.strip('|')
            parts = s.split(';')
            # parts: ['INFO', estado, nivel1, nivel2, nivel3, nivel4, temperatura]
            if len(parts) < 7:
                return {'state': self.state, 'levels': list(self.levels), 'temperature': self.temperature, 'message': resp}
            estado = parts[1]
            niveles = [int(float(x)) for x in parts[2:6]]
            temp = float(parts[6])
            # update internal values
            self.state = estado
            self.levels = niveles
            self.temperature = temp
            return {'state': estado, 'levels': niveles, 'temperature': temp, 'message': ''}
        except Exception:
            return {'state': self.state, 'levels': list(self.levels), 'temperature': self.temperature, 'message': resp}

    async def make(self, distribution: Dict[str, int], history_id: Optional[int] = None, user_id: Optional[int] = None):
        if self.state != 'IDLE':
            raise MachineBusyError('Machine is busy')

        # verify deposits
        for slot_str, ml in distribution.items():
            try:
                idx = int(slot_str) - 1
            except Exception:
                raise InsufficientDepositError('Invalid slot')
            if idx < 0 or idx >= len(self.levels):
                raise InsufficientDepositError('Invalid slot')
            if self.levels[idx] < ml:
                raise InsufficientDepositError(f'Insufficient level in slot {slot_str}')

        # build MAKE command string: MAKE;1=100;2=50;...
        parts = ['MAKE']
        for k, v in distribution.items():
            parts.append(f"{k}={int(v)}")
        make_cmd = ';'.join(parts)
        # send to hardware (or simulate)
        _ = await self._send_command(make_cmd)

        await self.lock.acquire()
        try:
            self.state = 'BUSY'
            # schedule background job
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._run_make(distribution, history_id, user_id))
            return {'status': 'started'}
        finally:
            # release immediately; the state variable prevents concurrent makes
            self.lock.release()

    async def _run_make(self, distribution: Dict[str, int], history_id: Optional[int], user_id: Optional[int]):
        total_ml = sum(distribution.values())
        # simulate time: 0.05s per ml min 2s
        duration = max(2, int(total_ml * 0.05))
        steps = max(1, duration)
        per_step = duration and (total_ml / steps)

        # simulate pouring
        poured = {k: 0 for k in distribution.keys()}
        for i in range(steps):
            await asyncio.sleep(1)
            # simple temperature rise
            self.temperature += 0.02 * (i + 1)

        # final consumption
        for slot_str, ml in distribution.items():
            idx = int(slot_str) - 1
            self.levels[idx] = max(0, self.levels[idx] - ml)

        # compute xp gained
        xp = max(1, total_ml // 50)

        # update DB history and user xp if provided
        try:
            db = SessionLocal()
            if history_id:
                h = db.query(History).filter(History.id == history_id).first()
                if h:
                    h.success = True
                    h.xp_gained = xp
                    db.add(h)
            if user_id:
                u = db.query(User).filter(User.id == user_id).first()
                if u:
                    u.xp = (u.xp or 0) + xp
                    db.add(u)
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass

        self.state = 'IDLE'

    async def clean(self):
        if self.state != 'IDLE':
            raise MachineBusyError('Machine busy')
        # send CLEAN command
        await self._send_command('CLEAN')
        self.state = 'BUSY'
        await asyncio.sleep(3)
        # simulate cleaning resets temperature mildly
        self.temperature = max(20.0, self.temperature - 2.0)
        self.state = 'IDLE'
        return {'status': 'cleaned'}

    async def stop(self):
        # stop running task if any
        # send STOP command
        await self._send_command('STOP')
        if self._task and not self._task.done():
            self._task.cancel()
        self.state = 'IDLE'
        return {'status': 'stopped'}

    async def set_temp(self, target: float):
        # send TEMP command
        await self._send_command(f'TEMP;{float(target)}')
        # this is a simulated setter
        self.temperature = float(target)
        return {'status': 'temp_set', 'temperature': self.temperature}
