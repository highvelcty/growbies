from typing import Optional
import logging
import time

from . import transport
from .structs import command

logger = logging.getLogger(__name__)


class Arduino(transport.ArduinoTransport):
    EXEC_RETRIES = 3
    EXEC_RETRY_DELAY_SEC = 0.25

    def execute(self, cmd: command.TBaseCommand, *,
                retries: int = EXEC_RETRIES,
                retry_delay_sec: float = EXEC_RETRY_DELAY_SEC) \
            -> Optional[command.TBaseResponse]:
        for retry in range(retries):
            if retry:
                time.sleep(retry_delay_sec)

            # Send
            self._send_cmd(cmd)

            # Receive
            self._slip_reset_recv_state()
            startt = time.time()
            while time.time() - startt < self.READ_TIMEOUT_SEC:
                resp = self._recv_resp()
                if resp is None:
                    logger.error(f'No response on retry {retry+1} / {retries}')
                else:
                    return resp
            else:
                logger.error(f'Timeout of {self.READ_TIMEOUT_SEC} seconds waiting for command '
                             f'response.')
        else:
            logger.error(f'Exhausted {self.EXEC_RETRIES} retries executing command:\n'
                         f'{cmd}')

    def sample(self) -> int:
        cmd = command.CmdSample()
        resp: command.RespLong = self.execute(cmd)
        return resp.data

    def wait_for_ready(self):
        cmd = command.CmdLoopback()
        resp: Optional[command.RespVoid] = (
            self.execute(cmd,
                         retries=self.READY_RETRIES,
                         retry_delay_sec=self.READY_RETRY_DELAY_SEC))
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
