"""
WebSocket connection manager and progress update helper.

Kept in a separate module to avoid circular imports between main.py and routes.
"""

import logging

logger = logging.getLogger(__name__)

active_connections: dict = {}


async def send_progress_update(review_id: str, progress: dict):
    """Send progress update to connected WebSocket clients."""
    if review_id in active_connections:
        try:
            await active_connections[review_id].send_json({
                "type": "progress",
                "data": progress
            })
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
