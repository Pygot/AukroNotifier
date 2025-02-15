from datetime import datetime


def log_it(message: str, message_type=1) -> None:
    time_now = datetime.now()

    match message_type:
        case 1: print(f"[{time_now}] - [INFO] : {message}")
        case 2: print(f"[{time_now}] - [ERROR] 🔴 : {message}")
        case _: print(f"[{time_now}] - [WHAT?!] 🔴: {message}")