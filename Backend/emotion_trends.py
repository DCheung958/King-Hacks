"""
Emotion Trend Analysis
Provides passive emotion trend visualization data
"""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict


async def get_emotion_trends(
    user_id: UUID,
    days: int = 30,
    limit: int = 100
) -> Dict[str, any]:
    """
    Get emotion trends over time for a user
    
    Args:
        user_id: User UUID
        days: Number of days to look back
        limit: Maximum number of messages to analyze
        
    Returns:
        Dictionary with emotion trend data
    """
    try:
        from db_operations import (
            get_conversations_by_user,
            get_messages_by_conversation
        )
        
        # Get user's conversations
        conversations = await get_conversations_by_user(user_id, limit=20)
        
        # Collect all messages with emotions
        all_messages = []
        for conv in conversations:
            conv_id = UUID(conv["id"])
            messages = await get_messages_by_conversation(conv_id, limit=limit)
            # Filter only user messages with emotions
            for msg in messages:
                if msg.get("role") == "user" and msg.get("emotion"):
                    all_messages.append({
                        "emotion": msg["emotion"],
                        "timestamp": msg.get("timestamp", conv.get("created_at", ""))
                    })
        
        if not all_messages:
            return {
                "emotions": {},
                "timeline": [],
                "summary": "No emotion data available"
            }
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get("timestamp", ""))
        
        # Calculate date range
        if all_messages:
            try:
                first_date = datetime.fromisoformat(all_messages[0]["timestamp"].replace('Z', '+00:00'))
                last_date = datetime.fromisoformat(all_messages[-1]["timestamp"].replace('Z', '+00:00'))
            except:
                # Fallback if timestamp parsing fails
                first_date = datetime.utcnow() - timedelta(days=days)
                last_date = datetime.utcnow()
        else:
            first_date = datetime.utcnow() - timedelta(days=days)
            last_date = datetime.utcnow()
        
        # Group emotions by time period (daily)
        emotion_by_day = defaultdict(lambda: defaultdict(int))
        emotion_counts = defaultdict(int)
        
        for msg in all_messages:
            emotion = msg["emotion"].lower()
            emotion_counts[emotion] += 1
            
            # Group by day
            try:
                timestamp = datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
                day_key = timestamp.date().isoformat()
                emotion_by_day[day_key][emotion] += 1
            except:
                # Use current date if parsing fails
                day_key = datetime.utcnow().date().isoformat()
                emotion_by_day[day_key][emotion] += 1
        
        # Build timeline data
        timeline = []
        for day in sorted(emotion_by_day.keys()):
            day_emotions = emotion_by_day[day]
            total = sum(day_emotions.values())
            timeline.append({
                "date": day,
                "emotions": {k: v / total if total > 0 else 0 for k, v in day_emotions.items()},
                "total_messages": total
            })
        
        # Calculate trends (simple: compare first half vs second half)
        mid_point = len(all_messages) // 2
        first_half = [m["emotion"].lower() for m in all_messages[:mid_point]]
        second_half = [m["emotion"].lower() for m in all_messages[mid_point:]]
        
        first_half_counts = defaultdict(int)
        second_half_counts = defaultdict(int)
        
        for emotion in first_half:
            first_half_counts[emotion] += 1
        for emotion in second_half:
            second_half_counts[emotion] += 1
        
        # Calculate changes
        trends = {}
        all_emotions = set(first_half_counts.keys()) | set(second_half_counts.keys())
        
        for emotion in all_emotions:
            first_count = first_half_counts.get(emotion, 0)
            second_count = second_half_counts.get(emotion, 0)
            first_pct = first_count / len(first_half) if first_half else 0
            second_pct = second_count / len(second_half) if second_half else 0
            
            change = second_pct - first_pct
            trends[emotion] = {
                "change": change,
                "direction": "up" if change > 0.05 else "down" if change < -0.05 else "stable",
                "first_half": first_pct,
                "second_half": second_pct
            }
        
        # Build summary
        top_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
        summary_parts = []
        
        if top_emotion:
            summary_parts.append(f"Most common emotion: {top_emotion}")
        
        # Add trend summary
        improving = [e for e, t in trends.items() if t["direction"] == "down" and e in ["sadness", "fear", "anger", "anxiety"]]
        if improving:
            summary_parts.append(f"Improving: {', '.join(improving)}")
        
        return {
            "emotions": dict(emotion_counts),
            "timeline": timeline,
            "trends": trends,
            "summary": ". ".join(summary_parts) if summary_parts else "Emotion data available",
            "total_messages": len(all_messages),
            "date_range": {
                "start": first_date.isoformat(),
                "end": last_date.isoformat()
            }
        }
        
    except Exception as e:
        print(f"Warning: Failed to get emotion trends: {e}")
        import traceback
        traceback.print_exc()
        return {
            "emotions": {},
            "timeline": [],
            "summary": f"Error: {str(e)}",
            "error": True
        }





