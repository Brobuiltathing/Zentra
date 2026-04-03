import asyncio
from datetime import datetime, timedelta, timezone

from config import (
    GOOGLE_AVAILABLE, ALLOWED_USER_IDS,
    MORNING_DIGEST_HOUR, MORNING_DIGEST_MINUTE,
    EVENT_REMINDER_MINUTES, EMAIL_POLL_INTERVAL_MINUTES,
)
from logger import log
from ollama import ollama_raw_sync
from actions.gmail import fetch_unread_emails_sync, importance_score, _format_email_digest
from actions.calendar import (
    _fetch_events_sync, _format_calendar_briefing,
    _extract_meeting_link, _fmt_event_time,
)
from utils.seen_emails import seen_email_ids, persist_seen_emails


class ZentraScheduler:
    def __init__(self, discord_client):
        self.client         = discord_client
        self._reminded_ids: set[str] = set()
        self._tasks:        list     = []

    def start(self):
        if not GOOGLE_AVAILABLE:
            log.warning("Google libraries not installed — scheduler disabled.")
            return
        self._tasks = [
            asyncio.create_task(self._morning_digest_loop()),
            asyncio.create_task(self._email_poll_loop()),
            asyncio.create_task(self._event_reminder_loop()),
        ]
        log.info("Scheduler started — morning digest, email poll, event reminders active.")

    def stop(self):
        for t in self._tasks:
            t.cancel()

    async def _dm(self, text: str):
        try:
            user = await self.client.fetch_user(ALLOWED_USER_IDS[0])
            for chunk in [text[i:i+1990] for i in range(0, len(text), 1990)]:
                await user.send(chunk)
        except Exception as exc:
            log.error(f"Scheduler DM failed: {exc}")

    @staticmethod
    async def _wait_until(hour: int, minute: int):
        now    = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

    async def _morning_digest_loop(self):
        while True:
            await self._wait_until(MORNING_DIGEST_HOUR, MORNING_DIGEST_MINUTE)
            try:
                await self._send_morning_digest()
            except Exception as exc:
                log.error(f"Morning digest error: {exc}")
            await asyncio.sleep(60)

    async def _send_morning_digest(self):
        log.info("Sending morning digest...")
        now_str      = datetime.now().strftime("%A %d %B %Y")
        header       = f"**Good morning! Here's your briefing for {now_str}**\n\n"
        emails       = await asyncio.to_thread(fetch_unread_emails_sync, 24)
        email_msg    = await asyncio.to_thread(_format_email_digest, emails)
        today_events = await asyncio.to_thread(_fetch_events_sync, 1)
        cal_msg      = _format_calendar_briefing(today_events, "Today")
        await self._dm(header + email_msg + "\n\n-----------\n\n" + cal_msg)

    async def _email_poll_loop(self):
        await asyncio.sleep(30)
        while True:
            try:
                emails = await asyncio.to_thread(fetch_unread_emails_sync, 1)
                for email in emails:
                    if email["id"] in seen_email_ids:
                        continue
                    score = await asyncio.to_thread(
                        importance_score,
                        email["sender"], email["subject"], email["snippet"]
                    )
                    if score >= 2:
                        summary = ollama_raw_sync(
                            "Summarise this important email in 2 sentences. Be direct and brief.",
                            f"Subject: {email['subject']}\n\n{email['body'] or email['snippet']}",
                            max_tokens=100,
                        )
                        urgency_label = "**Critical Email**" if score >= 3 else "**Important Email**"
                        await self._dm(
                            f"{urgency_label}\n"
                            f"**From:** {email['sender']}\n"
                            f"**Subject:** {email['subject']}\n"
                            f"**Summary:** {summary}"
                        )
                        log.info(f"Alert sent (score={score}): {email['subject']}")
                    seen_email_ids.add(email["id"])
                persist_seen_emails()
            except Exception as exc:
                log.error(f"Email poll error: {exc}")
            await asyncio.sleep(EMAIL_POLL_INTERVAL_MINUTES * 60)

    async def _event_reminder_loop(self):
        await asyncio.sleep(60)
        while True:
            try:
                now    = datetime.now(timezone.utc)
                events = await asyncio.to_thread(_fetch_events_sync, 1)
                for ev in events:
                    if ev["id"] in self._reminded_ids or not ev["start"]:
                        continue
                    if ev.get("all_day"):
                        continue
                    try:
                        start = datetime.fromisoformat(ev["start"].replace("Z", "+00:00"))
                    except Exception:
                        continue
                    delta = (start - now).total_seconds()
                    if 0 < delta <= EVENT_REMINDER_MINUTES * 60:
                        mins_away = int(delta / 60)
                        ts        = start.astimezone().strftime("%I:%M %p")
                        loc_line  = f"\nLocation: {ev['location']}"    if ev.get("location") else ""
                        link      = _extract_meeting_link(ev)
                        link_line = f"\nLink: {link}"                   if link               else ""
                        desc      = (ev.get("description") or "")[:100]
                        desc_line = f"\nNote: {desc}"                   if desc               else ""
                        await self._dm(
                            f"**Starting in {mins_away} min**\n"
                            f"**{ev['summary']}** at {ts}"
                            f"{loc_line}{link_line}{desc_line}"
                        )
                        self._reminded_ids.add(ev["id"])
                        log.info(f"Reminder sent: {ev['summary']} in {mins_away}m")
            except Exception as exc:
                log.error(f"Event reminder error: {exc}")
            await asyncio.sleep(60)
