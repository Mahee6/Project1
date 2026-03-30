from datetime import datetime, timezone
from typing import Dict, List, Any
from collections import defaultdict


class AnalyticsService:

    def __init__(self):
        self.message_cache = []

    def analyze_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not messages:
            return {"total": 0}

        stats = {
            "total": len(messages),
            "by_type": defaultdict(int),
            "by_conversation": defaultdict(int),
            "by_user": defaultdict(int),
            "media_count": 0,
            "text_count": 0,
            "time_range": {},
        }

        timestamps = []

        for msg in messages:
            msg_type = msg.get("message_type", "unknown")
            stats["by_type"][msg_type] += 1

            conv_id = msg.get("conversation_id", "unknown")
            stats["by_conversation"][conv_id] += 1

            user_phone = msg.get("user", {}).get("phone_number", "unknown")
            stats["by_user"][user_phone] += 1

            if msg_type in {"image", "video", "audio", "document", "sticker"}:
                stats["media_count"] += 1
            elif msg_type == "text":
                stats["text_count"] += 1

            ts = msg.get("timestamp")
            if ts:
                timestamps.append(ts)

        if timestamps:
            stats["time_range"] = {
                "earliest": datetime.fromtimestamp(min(timestamps), tz=timezone.utc).isoformat(),
                "latest": datetime.fromtimestamp(max(timestamps), tz=timezone.utc).isoformat(),
            }

        stats["by_type"] = dict(stats["by_type"])
        stats["by_conversation"] = dict(stats["by_conversation"])
        stats["by_user"] = dict(stats["by_user"])

        return stats

    def get_conversation_summary(self, messages: List[Dict[str, Any]], conversation_id: str) -> Dict[str, Any]:
        conv_messages = [m for m in messages if m.get("conversation_id") == conversation_id]

        if not conv_messages:
            return {"conversation_id": conversation_id, "message_count": 0}

        return {
            "conversation_id": conversation_id,
            "message_count": len(conv_messages),
            "participants": list(set(m.get("user", {}).get("phone_number") for m in conv_messages)),
            "message_types": list(set(m.get("message_type") for m in conv_messages)),
            "stats": self.analyze_messages(conv_messages),
        }

    def get_user_activity(self, messages: List[Dict[str, Any]], phone_number: str) -> Dict[str, Any]:
        user_messages = [
            m for m in messages if m.get("user", {}).get("phone_number") == phone_number
        ]

        if not user_messages:
            return {"phone_number": phone_number, "message_count": 0}

        return {
            "phone_number": phone_number,
            "message_count": len(user_messages),
            "conversations": list(set(m.get("conversation_id") for m in user_messages)),
            "stats": self.analyze_messages(user_messages),
        }
