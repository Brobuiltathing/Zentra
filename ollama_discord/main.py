import asyncio
import json
from pathlib import Path

import discord

from config import (
    DISCORD_BOT_TOKEN, OLLAMA_ENDPOINT, OLLAMA_MODEL,
    OLLAMA_VISION_MODEL, BASE_FOLDER, SCREENSHOT_FOLDER,
    MEMORY_DEPTH, ALLOWED_USER_IDS,
    PSUTIL_AVAILABLE, PYAUTOGUI_AVAILABLE, GOOGLE_AVAILABLE,
    MORNING_DIGEST_HOUR, MORNING_DIGEST_MINUTE,
    EVENT_REMINDER_MINUTES, EMAIL_POLL_INTERVAL_MINUTES,
)
from logger import log
from memory import load_memory, save_to_memory, build_prompt, user_locks
from ollama import query_ollama
from parser import extract_json
from dispatcher import dispatch_action, set_scheduler
from scheduler import ZentraScheduler
from utils.seen_emails import load_seen_emails


intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages     = True
client = discord.Client(intents=intents)

scheduler = None


async def keep_typing(channel, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        await channel.typing().__aenter__()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=8)
        except asyncio.TimeoutError:
            pass


async def process_message(user_id: int, user_input: str) -> str:
    prompt = build_prompt(user_id, user_input)

    try:
        raw_output = await query_ollama(prompt)
    except (ConnectionError, TimeoutError, RuntimeError) as exc:
        log.error(f"Ollama error: {exc}")
        return f"AI Error: {exc}"

    try:
        parsed = extract_json(raw_output)
        log.info(f"Parsed JSON:\n{json.dumps(parsed, indent=2)[:500]}")
    except ValueError as exc:
        log.error(f"JSON parse failure: {exc}")
        preview = raw_output[:800]
        return (
            f"Couldn't parse the AI's response as JSON.\n"
            f"Raw output:\n```\n{preview}\n```"
        )

    try:
        result, file_content = await dispatch_action(parsed)
    except Exception as exc:
        log.error(f"Dispatch error: {exc}", exc_info=True)
        return f"Action failed: {exc}"

    if file_content:
        filename = parsed.get("filename", "file")
        followup_prompt = (
            f"{user_input}\n\n"
            f"[ZENTRA NOTE: The file '{filename}' was read successfully. "
            f"Here is its content for you to reason about:]\n\n"
            f"```\n{file_content}\n```\n\n"
            f"Now answer the user's question about this file."
        )
        try:
            raw2    = await query_ollama(followup_prompt)
            parsed2 = extract_json(raw2)
            result2, _ = await dispatch_action(parsed2)
            result  = result + "\n\n" + result2
        except Exception as exc:
            log.warning(f"read_file follow-up failed: {exc}")
            result += "\n\nFile contents loaded into context."

    summary = (parsed.get("reply") or result)[:300]
    save_to_memory(user_id, user_input, summary)
    return result


async def send_response(channel, text: str) -> None:
    text = text or "Done."
    for chunk in [text[i:i+1990] for i in range(0, len(text), 1990)]:
        await channel.send(chunk)


@client.event
async def on_ready() -> None:
    global scheduler
    log.info("=" * 60)
    log.info("  ZENTRA v7.1 — AI Developer Assistant")
    log.info(f"  Bot user    : {client.user} (ID {client.user.id})")
    log.info(f"  Ollama      : {OLLAMA_ENDPOINT}  model={OLLAMA_MODEL}")
    log.info(f"  Vision model: {OLLAMA_VISION_MODEL}")
    log.info(f"  Base folder : {BASE_FOLDER}")
    log.info(f"  Screenshots : {SCREENSHOT_FOLDER}")
    log.info(f"  Memory depth: {MEMORY_DEPTH} exchanges per user")
    log.info(f"  psutil      : {'available' if PSUTIL_AVAILABLE else 'not installed'}")
    log.info(f"  pyautogui   : {'available' if PYAUTOGUI_AVAILABLE else 'not installed'}")
    log.info(f"  Google APIs : {'available' if GOOGLE_AVAILABLE else 'not installed'}")
    if GOOGLE_AVAILABLE:
        log.info(f"  Morning digest  : {MORNING_DIGEST_HOUR:02d}:{MORNING_DIGEST_MINUTE:02d} daily")
        log.info(f"  Event reminders : {EVENT_REMINDER_MINUTES} min before")
        log.info(f"  Email polling   : every {EMAIL_POLL_INTERVAL_MINUTES} min")
    if ALLOWED_USER_IDS:
        log.info(f"  Whitelist   : {ALLOWED_USER_IDS}")
    log.info("  Ready — waiting for DMs")
    log.info("=" * 60)

    load_memory()
    load_seen_emails()
    Path(BASE_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(SCREENSHOT_FOLDER).mkdir(parents=True, exist_ok=True)

    scheduler = ZentraScheduler(client)
    set_scheduler(scheduler)
    scheduler.start()


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user:
        return
    if not isinstance(message.channel, discord.DMChannel):
        return
    if ALLOWED_USER_IDS and message.author.id not in ALLOWED_USER_IDS:
        await message.channel.send("You're not authorised to use ZENTRA.")
        return

    user_input = message.content.strip()
    if not user_input:
        return

    user_id = message.author.id
    log.info(f"DM <- {message.author} ({user_id}): {user_input}")

    async with user_locks[user_id]:
        stop_event  = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(message.channel, stop_event))

        try:
            response = await process_message(user_id, user_input)
        finally:
            stop_event.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

    await send_response(message.channel, response)
    log.info(f"DM -> {message.author}: {response[:120]}...")


if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("No Discord bot token found!")
        print("Open config.py and replace YOUR_BOT_TOKEN_HERE with your real token.")
        raise SystemExit(1)

    if not PSUTIL_AVAILABLE:
        print("psutil not found — system_stats and close_app will be unavailable.")
    if not PYAUTOGUI_AVAILABLE:
        print("pyautogui not found — screen_action will be unavailable.")
    if not GOOGLE_AVAILABLE:
        print("Google libraries not found — Gmail/Calendar features disabled.")

    log.info("Starting ZENTRA v7.1...")
    client.run(DISCORD_BOT_TOKEN)
