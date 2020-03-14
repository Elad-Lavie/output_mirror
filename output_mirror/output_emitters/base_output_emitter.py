import abc

from output_mirror.output_subscribers.i_output_subscriber import IOutputSubscriber


class BaseOutputEmitter(abc.ABC):
    def __init__(self, output_subscriber: IOutputSubscriber):
        self._output_subscriber: IOutputSubscriber = output_subscriber

    @abc.abstractmethod
    async def start(self):
        pass

    async def _start_output_subscriber(self):
        await self._output_subscriber.on_start()

    async def _send_stdout_data(self, stdout_message: str):
        await self._output_subscriber.on_stdout(stdout_message)

    async def _send_stderr_data(self, stderr_message: str):
        await self._output_subscriber.on_stderr(stderr_message)

    async def _inform_no_more_data(self, extra_message):
        await self._output_subscriber.on_no_more_data(extra_message)

    def _should_exit_when_no_more_data(self):
        return self._output_subscriber.should_exit_when_no_more_data()


