import abc


class IOutputSubscriber(abc.ABC):

    @abc.abstractmethod
    async def on_start(self):
        pass

    @abc.abstractmethod
    async def on_stdout(self, stdout_message: str):
        pass

    @abc.abstractmethod
    async def on_stderr(self, stderr_message: str):
        pass

    @abc.abstractmethod
    async def on_no_more_data(self, extra_message: str):
        pass

    @abc.abstractmethod
    def should_exit_when_no_more_data(self):
        pass