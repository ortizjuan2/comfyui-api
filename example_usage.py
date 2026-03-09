"""Example usage of ComfyUI API client."""
import asyncio
from comfyui_api import ComfyClient


async def example_usage():
    """Demonstrate basic ComfyUI API usage."""
    
    # Initialize the client (adjust URL for your setup)
    client = ComfyClient("http://localhost:8188")
    
    try:
        # 1. Get available nodes and their inputs
        print("Fetching object info...")
        object_info = await client.get_object_info()
        
        # 2. Queue a simple prompt
        sample_prompt = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8.0,
                    "denoise": 1.0,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "positive": ["7", 0],
                    "negative": ["8", 0],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": 12345,
                    "steps": 20
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["6", 1],
                    "text": "a beautiful sunset"
                }
            },
            # ... add more nodes to complete your prompt structure
        }
        
        print("Queueing prompt...")
        prompt_id = await client.queue_prompt(sample_prompt)
        print(f"Prompt ID: {prompt_id}")
        
        # 3. Wait a bit for processing, then check history
        await asyncio.sleep(5)
        
        history = await client.get_history(prompt_id)
        if prompt_id in history:
            print(f"History for {prompt_id}:")
            for node_id, output in history[prompt_id]["outputs"].items():
                print(f"  Node {node_id}: {output.keys()}")
        
        # 4. Get system stats
        stats = await client.get_system_stats()
        print(f"System stats: {stats}")
        
    finally:
        # Always close the client when done
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
