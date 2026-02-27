"""Telegram update reader. Listens for all update types and extracts each update as a dict."""

from __future__ import annotations

import asyncio
import datetime as dtm
import importlib
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from dotenv import load_dotenv
from telegram import Update, Message, MessageEntity
from telegram._telegramobject import TelegramObject
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    ChosenInlineResultHandler,
    InlineQueryHandler,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    filters,
)

logger = logging.getLogger(__name__)

OnUpdate = Callable[[dict[str, Any]], Any] | Callable[[dict[str, Any]], Awaitable[Any]]

# ── Extraction helpers ────────────────────────────────────────────────────────

_MEDIA_FIELDS = ("photo", "animation", "audio", "document", "video", "voice", "video_note", "sticker")

_SERVICE_FIELDS = (
    "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo",
    "delete_chat_photo", "group_chat_created", "supergroup_chat_created",
    "channel_chat_created", "message_auto_delete_timer_changed",
    "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message",
    "successful_payment", "refunded_payment", "proximity_alert_triggered",
    "video_chat_scheduled", "video_chat_started", "video_chat_ended",
    "video_chat_participants_invited", "web_app_data",
    "forum_topic_created", "forum_topic_closed", "forum_topic_reopened",
    "forum_topic_edited", "general_forum_topic_hidden", "general_forum_topic_unhidden",
    "write_access_allowed", "users_shared", "chat_shared", "boost_added",
    "giveaway_created", "giveaway", "giveaway_winners", "giveaway_completed",
    "chat_background_set", "paid_message_price_changed",
)

# Optional handler classes that may not exist in all PTB versions
_OPTIONAL_HANDLERS = (
    ("telegram.ext", "ChatJoinRequestHandler"),
    ("telegram.ext", "ChatBoostHandler"),
    ("telegram.ext", "MessageReactionHandler"),
    ("telegram.ext._handlers.businessconnectionhandler", "BusinessConnectionHandler"),
    ("telegram.ext._handlers.businessmessagesdeletedhandler", "BusinessMessagesDeletedHandler"),
    ("telegram.ext._handlers.paidmediapurchasedhandler", "PaidMediaPurchasedHandler"),
)


def _to_dict(obj: Any) -> Any:
    """TelegramObject → dict, everything else passes through."""
    return obj.to_dict(recursive=True) if isinstance(obj, TelegramObject) else obj


def _entity_text(text: str, offset: int, length: int) -> str:
    """Slice entity text using UTF-16 offsets (what Telegram uses)."""
    encoded = text.encode("utf-16-le")
    return encoded[offset * 2 : (offset + length) * 2].decode("utf-16-le", errors="replace")


def _extract_entities(entities: tuple[MessageEntity, ...] | None, text: str | None) -> list[dict] | None:
    if not entities:
        return None
    out = []
    for e in entities:
        d: dict[str, Any] = {"type": e.type, "offset": e.offset, "length": e.length}
        if e.url:
            d["url"] = e.url
        if e.user:
            d["user"] = _to_dict(e.user)
        if e.language:
            d["language"] = e.language
        if text:
            d["text"] = _entity_text(text, e.offset, e.length)
        out.append(d)
    return out


def _extract_media(msg: Message) -> list[dict] | None:
    media = []
    for field in _MEDIA_FIELDS:
        obj = getattr(msg, field, None)
        if not obj:
            continue
        if field == "photo":
            largest = max(obj, key=lambda p: (p.width or 0) * (p.height or 0))
            media.append({"type": "photo", **_to_dict(largest), "all_sizes": [_to_dict(s) for s in obj]})
        else:
            d = {"type": field, **_to_dict(obj)}
            dur = getattr(obj, "duration", None)
            if isinstance(dur, dtm.timedelta):
                d["duration"] = dur.total_seconds()
            media.append(d)
    return media or None


def _detect_service(msg: Message) -> tuple[str | None, Any]:
    for field in _SERVICE_FIELDS:
        val = getattr(msg, field, None)
        if val is None:
            continue
        if isinstance(val, bool) and not val:
            continue
        if isinstance(val, (tuple, list)):
            if not val:
                continue
            return field, [_to_dict(v) for v in val]
        return field, _to_dict(val)
    return None, None


def _update_type(update: Update) -> str:
    for slot in Update.__slots__:
        if not slot.startswith("_") and slot != "update_id" and getattr(update, slot, None) is not None:
            return slot
    return "unknown"


def extract(update: Update) -> dict[str, Any]:
    """Convert a telegram.Update into a plain dict with all available data."""
    data: dict[str, Any] = {
        "update_id": update.update_id,
        "type": _update_type(update),
        "timestamp": dtm.datetime.now(dtm.timezone.utc).isoformat(),
        "raw": update.to_dict(recursive=True),
    }

    u = update.effective_user
    if u:
        data["user"] = _to_dict(u)
    c = update.effective_chat
    if c:
        data["chat"] = _to_dict(c)

    msg = update.effective_message
    if msg:
        data["message_id"] = msg.message_id
        data["date"] = msg.date.isoformat() if msg.date else None
        if msg.edit_date:
            data["edit_date"] = msg.edit_date.isoformat()
        if msg.text:
            data["text"] = msg.text
        if msg.caption:
            data["caption"] = msg.caption
        ents = _extract_entities(msg.entities, msg.text)
        if ents:
            data["entities"] = ents
        cap_ents = _extract_entities(msg.caption_entities, msg.caption)
        if cap_ents:
            data["caption_entities"] = cap_ents
        media = _extract_media(msg)
        if media:
            data["media"] = media
        if msg.reply_to_message:
            r = msg.reply_to_message
            data["reply_to"] = {"message_id": r.message_id, "text": r.text, "from": _to_dict(r.from_user)}
        fwd = getattr(msg, "forward_origin", None)
        if fwd:
            data["forward_origin"] = _to_dict(fwd)
        if msg.reply_markup and hasattr(msg.reply_markup, "inline_keyboard"):
            data["reply_markup"] = [[_to_dict(btn) for btn in row] for row in msg.reply_markup.inline_keyboard]
        if msg.contact:
            data["contact"] = _to_dict(msg.contact)
        if msg.location:
            data["location"] = _to_dict(msg.location)
        if msg.venue:
            data["venue"] = _to_dict(msg.venue)
        if msg.poll:
            data["poll"] = _to_dict(msg.poll)
        if msg.dice:
            data["dice"] = {"emoji": msg.dice.emoji, "value": msg.dice.value}
        svc_type, svc_data = _detect_service(msg)
        if svc_type:
            data["service"] = {"type": svc_type, "data": svc_data}

    if update.callback_query:
        cq = update.callback_query
        data["callback_query"] = {
            "id": cq.id, "data": cq.data, "from": _to_dict(cq.from_user),
            "message": _to_dict(cq.message) if cq.message else None,
        }

    return data


# ── Bot reader ────────────────────────────────────────────────────────────────

class TelegramUpdateReader:
    """Listens for all Telegram bot updates and delivers extracted dicts to a callback.

    Usage:
        from commlinkio.telegram.readers import TelegramUpdateReader

        def handle(data: dict):
            print(data)

        reader = TelegramUpdateReader(on_update=handle)
        reader.start()
    """

    def __init__(self, token: str | None = None, on_update: OnUpdate | None = None):
        load_dotenv()
        self._token = token or os.environ["TELEGRAM_BOT_TOKEN"]
        self._on_update = on_update
        self._app: Application | None = None

    def on_update(self, fn: OnUpdate) -> OnUpdate:
        """Decorator to set the callback."""
        self._on_update = fn
        return fn

    def _build(self) -> Application:
        app = ApplicationBuilder().token(self._token).build()

        app.add_handler(MessageHandler(filters.ALL, self._handle))
        app.add_handler(CallbackQueryHandler(self._handle))
        app.add_handler(InlineQueryHandler(self._handle))
        app.add_handler(ChosenInlineResultHandler(self._handle))
        app.add_handler(ShippingQueryHandler(self._handle))
        app.add_handler(PreCheckoutQueryHandler(self._handle))
        app.add_handler(PollHandler(self._handle))
        app.add_handler(PollAnswerHandler(self._handle))
        app.add_handler(ChatMemberHandler(self._handle, ChatMemberHandler.MY_CHAT_MEMBER))
        app.add_handler(ChatMemberHandler(self._handle, ChatMemberHandler.CHAT_MEMBER))

        for mod_path, cls_name in _OPTIONAL_HANDLERS:
            try:
                cls = getattr(importlib.import_module(mod_path), cls_name)
                app.add_handler(cls(self._handle))
            except Exception:
                pass

        app.add_error_handler(self._on_error)
        return app

    async def _handle(self, update: Update, context: Any) -> None:
        try:
            data = extract(update)
            if self._on_update:
                result = self._on_update(data)
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result
        except Exception:
            logger.exception("Error processing update %s", update.update_id)

    async def _on_error(self, update: object, context: Any) -> None:
        logger.error("Bot error: %s", context.error, exc_info=context.error)

    def start(self) -> None:
        """Start polling (blocking). Ctrl+C to stop."""
        self._app = self._build()
        logger.info("Telegram reader started.")
        self._app.run_polling(allowed_updates=list(Update.ALL_TYPES), drop_pending_updates=True)

    async def start_async(self) -> None:
        """Start polling (non-blocking, for use inside an existing event loop)."""
        self._app = self._build()
        await self._app.initialize()
        if self._app.updater:
            await self._app.updater.start_polling(allowed_updates=list(Update.ALL_TYPES), drop_pending_updates=True)
        await self._app.start()

    async def stop(self) -> None:
        """Stop the bot."""
        if self._app:
            if self._app.updater and self._app.updater.running:
                await self._app.updater.stop()
            if self._app.running:
                await self._app.stop()
            await self._app.shutdown()

# Backward compatibility alias.
TelegramReader = TelegramUpdateReader
