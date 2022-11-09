import asyncio
import eel
from threading import Thread
import re

eel.init("web", allowed_extensions=[".js", ".html"])

layer = 0


def get_layer_from_qmk_console_printout(printout):
    print(printout)
    matches = re.search(r"layer(\d)$", printout)
    if matches is not None:
        return int(matches.group(1))
    else:
        return None


async def update_layer():
    global layer
    proc = await asyncio.subprocess.create_subprocess_shell(
        "qmk console", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    while True:
        printout = await proc.stdout.read(1024)
        printout = printout.decode("utf-8")
        newlayer = get_layer_from_qmk_console_printout(printout=printout)
        if newlayer is not None:
            layer = newlayer
            print(f"Layer changed to {layer}")


def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_layer())


def start_qmk_thread() -> None:
    loop = asyncio.new_event_loop()
    t = Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    return t


@eel.expose()
def get_image_path():
    print("get_image_path called")
    ret = f"static/layer{layer}.png"
    print(ret)
    return ret


qmk_thread = start_qmk_thread()

# clean up the qmk thread on quit
eel.start("index.html", port=5000, close_callback=qmk_thread.join)
