import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import websockets
from pypresence import Presence

CLIENT_ID = "1438919126906179778"
rpc = None
executor = ThreadPoolExecutor(max_workers=1)


# Persistent Discord connection
async def connect_rpc():
    global rpc
    loop = asyncio.get_event_loop()
    while True:
        try:
            rpc = await loop.run_in_executor(executor, lambda: Presence(CLIENT_ID))
            await loop.run_in_executor(executor, rpc.connect)
            print("[RPC] Connected to Discord")
            break
        except Exception as e:
            print(
                f"[RPC] Discord not running yet or connection lost, retrying in 5s... Error: {e}"
            )
            await asyncio.sleep(5)


async def safe_update(details, chapter, author):
    global rpc
    loop = asyncio.get_event_loop()

    details_line = details
    if chapter:
        details_line = f"{details_line} - {chapter}"

    state_line = f"Author: {author}" if author else ""

    try:
        await loop.run_in_executor(
            executor,
            lambda: rpc.update(
                details=details_line,
                state=state_line,
                large_image="ao3",
                large_text="An Archive Of Our Own",
            ),
        )
    except Exception as e:
        print(f"[RPC] Discord update failed, reconnecting: {e}")
        await connect_rpc()
        try:
            await loop.run_in_executor(
                executor,
                lambda: rpc.update(
                    details=details_line,
                    state=state_line,
                    large_image="ao3",
                    large_text="An Archive Of Our Own",
                ),
            )
        except Exception as e2:
            print(f"[RPC] Second attempt failed: {e2}")


# AO3 title parser
def parse_ao3_title(raw):
    parts = [p.strip() for p in raw.split(" - ")]

    fic_name = "Unknown Fic"
    chapter = ""
    author = ""

    if len(parts) > 0:
        fic_name = parts[0]

    if len(parts) > 1 and "Chapter" not in parts[1]:
        author = parts[1]

    for part in parts:
        if "Chapter" in part:
            chapter = part
            # if the author was incorrectly identified as the chapter, clear it
            if author == chapter:
                author = ""

    if not author and len(parts) > 2 and "Chapter" not in parts[2]:
        author = parts[2]

    return fic_name, chapter, author


# WebSocket handler
async def handler(ws):
    async for message in ws:
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "clear":
                if rpc:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(executor, rpc.clear)
                print("[RPC] Presence cleared")
                continue

            fic_name, chapter, author = parse_ao3_title(data["title"])

            details_line = f"Reading: {fic_name}"

            await safe_update(details_line, chapter, author)
            print(
                f"[RPC] Updated Discord -> {details_line} | Chapter: {chapter or '(no chapter)'} | Author: {author or '(no author)'}"
            )
        except Exception as e:
            print(f"[RPC] Error handling message: {e}")


# Main WebSocket server
async def main():
    await connect_rpc()
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("[WS] Relay running on ws://localhost:8765")
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if rpc:
            rpc.close()
    finally:
        executor.shutdown(wait=False)
