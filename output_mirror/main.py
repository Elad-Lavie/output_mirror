#!/usr/bin/env python

import argparse
import asyncio
import sys
import os

from output_mirror.output_subscribers.telegram_subscriber import TelegramSubscriber
from output_mirror.output_emitters.subprocess_output_emitter import SubprocessOutputEmitter, OnReceivingCtrlC


def _parse_args():
    parser = argparse.ArgumentParser(description="script to send process output to telegram")

    parser.add_argument("--on_receiving_ctrl_c", default=OnReceivingCtrlC.SEND_CTRL_C_TO_SUBPROCESS,
                        type=OnReceivingCtrlC, choices=list(OnReceivingCtrlC))

    def add_with_environment_variable(argument, env_name: str):
        environment_value = os.environ.get(env_name)
        if environment_value is not None:
            parser.add_argument(argument, default=environment_value)
        else:
            parser.add_argument(argument, required=True,
                                help=f"tip: add {env_name} as environment variable instead of passing {argument} "
                                     "to this script")

    add_with_environment_variable("--telegram_token", "TELEGRAM_CLIENT_TOKEN")

    add_with_environment_variable("--chat_id", "TELEGRAM_CLIENT_CHAT_ID")

    parser.add_argument("--args", nargs="+", required=True,
                        help="if running python script, please run with -u.\n"
                             f"for example:\n {sys.argv[0]} --args python -u hello.py")

    return parser.parse_args()


def main():
    args = _parse_args()

    command = " ".join(args.args)

    subprocess_telegram_client = SubprocessOutputEmitter(command,
                                                         args.on_receiving_ctrl_c,
                                                         TelegramSubscriber(args.telegram_token, args.chat_id))

    asyncio.run(subprocess_telegram_client.start())


if __name__ == "__main__":
    main()
