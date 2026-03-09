"""ComfyUI API Client - A wrapper for interacting with ComfyUI's REST API."""
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class QueueItem:
    """Represents a queued or running task."""
    prompt_id: str
    status: str  # 'queued', 'running', 'history'
    output: Optional[Dict[str, Any]] = None
    history_outputs: Optional[Dict[str, Any]] = None


class ComfyUIAPIError(Exception):
    """Exception raised for API errors."""
    pass


class ComfyClient:
    """Client for interacting with ComfyUI's HTTP API.
    
    Args:
        base_url: Base URL of ComfyUI server (e.g., 'http://localhost:8188')
        timeout: Request timeout in seconds (default: 60)
        
    Example:
        >>> client = ComfyClient('http://localhost:8188')
        >>> client.get_history()
        >>> result_id = client.queue_prompt(prompt_data)
        >>> outputs = client.get_outputs(result_id)
    """
    
    def __init__(self, base_url: str = "http://localhost:8188", timeout: float = 60.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
    
    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()
    
    # ==================== Prompt Queue Methods ====================
    
    async def get_queue(self) -> List[Dict[str, Any]]:
        """Get current queued and running prompts.
        
        Returns:
            List of prompt queue items with their status.
        """
        try:
            response = await self._client.get(f"{self.base_url}/prompt")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to get queue: {e}")
    
    async def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        """Queue a prompt for execution.
        
        Args:
            prompt: The ComfyUI prompt JSON structure
            
        Returns:
            The prompt_id of the queued task
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/prompt",
                json=prompt,
            )
            response.raise_for_status()
            result = response.json()
            return result['prompt_id']
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to queue prompt: {e}")
    
    async def interrupt_prompt(self):
        """Interrupt the currently running prompt."""
        try:
            await self._client.post(f"{self.base_url}/interrupt")
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to interrupt prompt: {e}")
    
    async def clear_queue(self):
        """Clear all queued prompts."""
        try:
            await self._client.post(f"{self.baseur}/queue")
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to clear queue: {e}")
    
    # ==================== History Methods ====================
    
    async def get_history(self, prompt_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution history.
        
        Args:
            prompt_id: Optional specific prompt ID to get history for
            
        Returns:
            Dict of prompt histories with outputs and timings.
        """
        try:
            if prompt_id:
                response = await self._client.get(
                    f"{self.base_url}/history/{prompt_id}"
                )
            else:
                response = await self._client.get(f"{self.base_url}/history")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to get history: {e}")
    
    # ==================== Output Methods ====================
    
    async def get_outputs(self, prompt_id: str) -> Dict[str, Any]:
        """Get outputs and images for a specific prompt.
        
        Args:
            prompt_id: The ID of the executed prompt
            
        Returns:
            Dict containing outputs including image URLs.
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/view",
                params={"filename": "output.png"},  # Adjust based on your needs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to get outputs: {e}")
    
    async def download_image(self, prompt_id: str, node_id: str) -> bytes:
        """Download an image output from a completed prompt.
        
        Args:
            prompt_id: The prompt execution ID
            node_id: The node that generated the image
            
        Returns:
            Image bytes
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/view",
                params={
                    "prompt_id": prompt_id,
                    "filename": f"{node_id}_image.png"
                }
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to download image: {e}")
    
    # ==================== System & Device Methods ====================
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system and GPU statistics."""
        try:
            response = await self._client.get(f"{self.base_url}/system_stats")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to get system stats: {e}")
    
    async def get_object_info(self) -> Dict[str, Any]:
        """Get information about available nodes and their inputs/outputs."""
        try:
            response = await self._client.get(f"{self.base_url}/object_info")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to get object info: {e}")
    
    async def list_models(self, device: str = "all") -> List[str]:
        """List available models.
        
        Args:
            device: Filter by device ('cpu', 'cuda', 'mps', or 'all')
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/object_info",
                params={"device": device}
            )
            response.raise_for_status()
            data = response.json()
            # Extract model paths from the structure
            return list(data.get("ComfyUI-Manager-Models-Vendor", {}).keys()) if "ComfyUI-Manager" in str(data) else []
        except httpx.HTTPStatusError as e:
            raise ComfyUIAPIError(f"Failed to list models: {e}")
