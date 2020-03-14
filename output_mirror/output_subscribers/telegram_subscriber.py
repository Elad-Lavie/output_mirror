import functools
import sys
from typing import List

import requests
import asyncio

from output_mirror.output_subscribers.i_output_subscriber import IOutputSubscriber


class TelegramSubscriber(IOutputSubscriber):
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, telegram_token: str, chat_id: int, min_time_between_messages_in_seconds=30):
        self._url = "https://api.telegram.org/" + "bot" + telegram_token + "/sendMessage" + "?chat_id=" + str(chat_id)
        self._output_to_send: List[str] = []
        self._min_time_between_messages = min_time_between_messages_in_seconds

        self._worker_task = None

    async def on_start(self):
        self._worker_task = asyncio.create_task(self._telegram_worker())

    async def on_stdout(self, stdout_from_subprocess: str):
        self._output_to_send.append(stdout_from_subprocess)

    async def on_stderr(self, stderr_from_subprocess: str):
        self._output_to_send.append(stderr_from_subprocess)

    async def on_no_more_data(self, extra_message):
        self._worker_task.cancel()

        data_to_send = "".join(self._output_to_send) + \
                       f"\n{extra_message}"
        self._send_to_telegram(data_to_send)

    def should_exit_when_no_more_data(self):
        return True

    async def _telegram_worker(self):
        try:
            while True:
                sleep_interval = self._min_time_between_messages

                if self._output_to_send:
                    data_to_send = "".join(self._output_to_send)
                    self._output_to_send = []
                    self._send_to_telegram(data_to_send)

                await asyncio.sleep(sleep_interval)
        except asyncio.CancelledError:
            pass

    def _send_to_telegram(self, message: str):
        reply = requests.post(self._url, json={'text': message[-self.MAX_MESSAGE_LENGTH:]})
        if not reply.ok:
            print("error sending message to telegram:\n" + reply.text, file=sys.stderr, end="")
