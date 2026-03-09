# comfyui-api

A Python wrapper for ComfyUI's HTTP API. Provides both async and sync interfaces for interacting with ComfyUI programmatically.

## Installation

```bash
pip install httpx
# Copy this package to your project, or install locally:
# pip install -e .
```

## Quick Start

### Async usage (recommended):

```python
import asyncio
from comfyui_api import ComfyClient


async def main():
    client = ComfyClient("http://localhost:8188")
    
    try:
        # Queue a prompt
        prompt_id = await client.queue_prompt(my_prompt)
        
        # Get history and outputs
        history = await client.get_history(prompt_id)
        
        # System info
        stats = await client.get_system_stats()
        
    finally:
        await client.close()


asyncio.run(main())
```

### Sync usage:

```python
from comfyui_api import SyncComfyClient


client = SyncComfyClient("http://localhost:8188")

# Queue a prompt
prompt_id = client.queue_prompt(my_prompt)

# Get history
history = client.get_history(prompt_id)

client.close()
```

## Features

- ✅ Async support (using `httpx` async client)
- ✅ Sync wrapper for non-async codebases
- ✅ All core endpoints covered:
  - `/prompt` - Queue and manage prompts
  - `/history` - Get execution history
  - `/system_stats` - GPU and system info
  - `/object_info` - Available nodes and parameters
- ✅ Typed dataclasses for structured responses
- ✅ Proper error handling with `ComfyUIAPIError`

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/prompt` | POST/GET | Queue prompts, get current queue |
| `/interrupt` | POST | Interrupt running prompt |
| `/queue` | POST | Clear queue |
| `/history/{id}` | GET | Get specific prompt history |
| `/view` | GET | Get outputs/images |
| `/system_stats` | GET | System resource info |
| `/object_info` | GET | Available nodes and params |

## Requirements

- Python 3.8+
- httpx (async HTTP client)
- Running ComfyUI instance

## Error Handling

```python
from comfyui_api import ComfyUIAPIError

try:
    result = await client.queue_prompt(prompt)
except ComfyUIAPIError as e:
    print(f"API error: {e}")
```

## Notes

- Make sure ComfyUI is running and listening on the specified port (default: 8188)
- For production use, consider adding retry logic to your code
- Images are typically downloaded via `/view` endpoint with appropriate query params
- Adjust prompt structure based on your custom nodes and workflow

## License

MIT - Feel free to use and modify as needed.
