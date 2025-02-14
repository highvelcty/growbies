from typing import Optional
import logging
import time

from . import transport
from .structs import command

logger = logging.getLogger(__name__)


class Arduino(transport.ArduinoTransport):
    EXEC_RETRIES = 3

    RESET_COMMUNICATION_LOOPS = 3
    RESET_COMMUNICATION_LOOP_DELAY = 0.33

    def execute(self, cmd: command.TBaseCommand, *,
                retries: int = EXEC_RETRIES) \
            -> Optional[command.TBaseResponse]:
        for retry in range(retries):
            if retry:
                self.reset_communication()
                # time.sleep(retry_delay_sec)

            # Send
            self._send_cmd(cmd)

            # Receive
            resp = self._recv_resp()
            if resp is None:
                logger.error(f'Execution layer no response on retry {retry+1} / {retries}')
            elif isinstance(resp, command.RespError):
                logger.error(f'Execution layer error response 0x{resp.error:04X} received.')
            else:
                return resp
        else:
            logger.error(f'Execution layer exhausted {self.EXEC_RETRIES} retries executing '
                         f'command:\n{cmd}')

    def read_average(self, times: int = command.CmdReadAverage.DEFAULT_TIMES) -> int:
        cmd = command.CmdReadAverage(times=times)
        resp: command.RespLong = self.execute(cmd)
        return resp.data

    def reset_communication(self):
        for _ in range(self.RESET_COMMUNICATION_LOOPS):
            self._slip_send_end()

            startt = time.time()
            while time.time() - startt < self.RESET_COMMUNICATION_LOOP_DELAY:
                bytes_in_waiting = self.in_waiting
                if bytes_in_waiting:
                    _ = self.read(bytes_in_waiting)

    def wait_for_ready(self):
        cmd = command.CmdLoopback()
        resp: Optional[command.RespVoid] = (
            self.execute(cmd,
                         retries=self.READY_RETRIES))
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
