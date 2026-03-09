"""Sync wrapper for ComfyUI API client."""
import asyncio
from .client import ComfyClient, ComfyUIAPIError


class SyncComfyClient:
    """Synchronous wrapper around ComfyClient for non-async code."""
    
    def __init__(self, base_url: str = "http://localhost:8188", timeout: float = 60.0):
        self._client = ComfyClient(base_url, timeout)
        self.base_url = base_url
    
    def close(self):
        """Close the async client."""
        try:
            asyncio.get_event_loop().run_until_complete(self._client.close())
        except RuntimeError:
            # If no running loop, create one just for this
            asyncio.new_event_loop().run_until_complete(self._client.close())
    
    def get_queue(self):
        """Get current queued prompts."""
        return asyncio.get_event_loop().run_until_complete(
            self._client.get_queue()
        )
    
    def queue_prompt(self, prompt: dict) -> str:
        """Queue a prompt for execution."""
        return asyncio.get_event_loop().run_until_complete(
            self._client.queue_prompt(prompt)
        )
    
    def get_history(self, prompt_id: str = None):
        """Get execution history."""
        return asyncio.get_event_loop().run_until_complete(
            self._client.get_history(prompt_id)
        )
    
    def interrupt_prompt(self):
        """Interrupt running prompt."""
        asyncio.get_event_loop().run_until_complete(
            self._client.interrupt_prompt()
        )
