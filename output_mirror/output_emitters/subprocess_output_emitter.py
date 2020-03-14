import asyncio
import signal
import enum
from functools import partial
import sys

from output_mirror.output_emitters.base_output_emitter import BaseOutputEmitter
from output_mirror.output_subscribers.i_output_subscriber import IOutputSubscriber


class OnReceivingCtrlC(enum.Enum):
    SEND_CTRL_C_TO_SUBPROCESS = "send_ctrl_c_to_subprocess"
    KILL_SUBPROCESS_AND_EXIT = "kill_subprocess_and_exit"

    def __str__(self):
        return self.value


class SubprocessOutputEmitter(BaseOutputEmitter):
    def __init__(self, command, on_receiving_ctrl_c: OnReceivingCtrlC, output_subscriber: IOutputSubscriber):

        super().__init__(output_subscriber)

        self._on_receiving_ctrl_c = on_receiving_ctrl_c

        self._command = command

        self._subprocess_transport = None

        self._exit_future = None

        self._process_exit_task = None

    def on_stdout_from_subprocess(self, stdout_from_subprocess: bytes):
        decoded_stdout = stdout_from_subprocess.decode()
        print(decoded_stdout, file=sys.stdout, end="")
        asyncio.create_task(self._send_stdout_data(decoded_stdout))

    def on_stderr_from_subprocess(self, stderr_from_subprocess: bytes):
        decoded_stderr = stderr_from_subprocess.decode()
        print(decoded_stderr, file=sys.stderr, end="")
        asyncio.create_task(self._send_stderr_data(decoded_stderr))

    def on_subprocess_exit(self, return_code: int):
        info_to_send = f"subprocess exited, return code is {return_code}"
        print(info_to_send)
        asyncio.create_task(self._inform_no_more_data(info_to_send))
        if self._should_exit_when_no_more_data():
            self._exit_future.set_result(True)

    async def start(self):
        loop = asyncio.get_running_loop()

        loop.add_signal_handler(signal.SIGINT, self._on_receiving_ctrl_c_handler)

        self._exit_future = loop.create_future()

        self._subprocess_transport, _ = await loop.subprocess_shell(partial(SubprocessProtocol,
                                                                            self.on_stdout_from_subprocess,
                                                                            self.on_stderr_from_subprocess,
                                                                            self.on_subprocess_exit),
                                                                    self._command,
                                                                    stdin=sys.stdin)

        await self._start_output_subscriber()

        try:
            await self._exit_future

        finally:
            self._subprocess_transport.close()

            current_task = asyncio.current_task()
            pending = [task for task in asyncio.all_tasks() if task != current_task]
            await asyncio.gather(*pending)

    def _on_receiving_ctrl_c_handler(self):
        if self._is_subprocess_running():
            operation = self._on_receiving_ctrl_c

            if operation == OnReceivingCtrlC.SEND_CTRL_C_TO_SUBPROCESS:
                self._subprocess_transport.send_signal(signal.SIGINT)
            elif operation == OnReceivingCtrlC.KILL_SUBPROCESS_AND_EXIT:
                self._subprocess_transport.kill()

    def _is_subprocess_running(self):
        is_subprocess_started = self._subprocess_transport is not None
        return is_subprocess_started and self._subprocess_transport.get_returncode() is None


class SubprocessProtocol(asyncio.SubprocessProtocol):
    def __init__(self, on_stdout_from_subprocess, on_stderr_from_subprocess, on_subprocess_exit):
        self._on_stdout_from_subprocess = on_stdout_from_subprocess
        self._on_stderr_from_subprocess = on_stderr_from_subprocess
        self._on_subprocess_exit = on_subprocess_exit

        self._transport = None

    def connection_made(self, transport: asyncio.SubprocessTransport) -> None:
        self._transport = transport

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self._on_stdout_from_subprocess(data)
        elif fd == 2:
            self._on_stderr_from_subprocess(data)
        else:
            assert False

    def process_exited(self):
        self._on_subprocess_exit(self._transport.get_returncode())
