"""Batch runner for ComfyUI workflows with dynamic prompts."""
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from comfyui_api import ComfyClient


class WorkflowRunner:
    """Runs ComfyUI workflows from JSON files with dynamic prompt modification.
    
    Args:
        workflow_path: Path to your saved workflow JSON file
        client: Optional ComfyClient instance (creates one if not provided)
        
    Example:
        >>> runner = WorkflowRunner('my_workflow.json')
        >>> await runner.run(prompt="a cat in space")
        >>> await runner.batch_run(prompts=["prompt1", "prompt2"], max_concurrent=2)
    """
    
    def __init__(self, workflow_path: Union[str, Path], base_url: str = "http://localhost:8188"):
        self.workflow_path = Path(workflow_path)
        self.base_url = base_url
        self.client = ComfyClient(base_url)
        
        # Load and cache the workflow template
        with open(self.workflow_path, 'r') as f:
            self._workflow_template = json.load(f)
    
    async def run(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
        custom_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run the workflow with modified parameters.
        
        Args:
            prompt: The text prompt to use
            negative_prompt: Optional negative prompt (if workflow has CLIPTextEncode for it)
            seed: Override random seed (None keeps random)
            steps: Override number of sampling steps
            cfg_scale: Override CFG scale
            custom_inputs: Extra node inputs to modify
            
        Returns:
            Dict with prompt_id and final prompt data used
        """
        # Deep copy template so we don't modify the original
        workflow = json.loads(json.dumps(self._workflow_template))
        
        # Find CLIPTextEncode nodes (where prompts go)
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') == 'CLIPTextEncode':
                # Modify positive prompt
                if 'text' in node_data['inputs']:
                    node_data['inputs']['text'] = prompt
                
                # Try to modify negative prompt if there's a second CLIPTextEncode
                break  # Found first one, move on
        
        # Apply other overrides
        if seed is not None:
            workflow = self._apply_seed(workflow, seed)
        
        if steps is not None:
            workflow = self._apply_steps(workflow, steps)
        
        if cfg_scale is not None:
            workflow = self._apply_cfg_scale(workflow, cfg_scale)
        
        # Apply custom inputs (more granular control)
        if custom_inputs:
            workflow = self._apply_custom_inputs(workflow, custom_inputs)
        
        print(f"Running with prompt: '{prompt}'")
        
        # Queue the modified workflow
        result = await self.client.queue_prompt(workflow)
        prompt_id = result['prompt_id']
        
        return {
            'prompt_id': prompt_id,
            'workflow_used': workflow
        }
    
    async def batch_run(
        self,
        prompts: List[str],
        output_dir: Optional[Path] = None,
        max_concurrent: int = 1,
        **run_kwargs
    ) -> Dict[str, str]:
        """Run multiple prompts in parallel up to concurrency limit.
        
        Args:
            prompts: List of text prompts to run
            output_dir: Directory to save status logs (optional)
            max_concurrent: Maximum simultaneous jobs
            **run_kwargs: Additional kwargs passed to each .run() call
            
        Returns:
            Dict mapping prompt -> prompt_id
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(prompt_text: str, idx: int) -> tuple[str, str]:
            async with semaphore:
                result = await self.run(prompt=prompt_text, **run_kwargs)
                return (prompt_text, result['prompt_id'])
        
        tasks = [run_with_stdio(p, i) for i, p in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        
        # Optionally write status file
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = output_dir / "run_log.json"
            log_data = {prompt: prompt_id for prompt, prompt_id in results}
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        
        return dict(results)
    
    def _apply_seed(self, workflow: Dict, seed: int) -> Dict:
        """Find and apply seed override to KSampler nodes."""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') == 'KSampler':
                workflow[node_id]['inputs']['seed'] = seed
        return workflow
    
    def _apply_steps(self, workflow: Dict, steps: int) -> Dict:
        """Find and apply step count to KSampler nodes."""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') == 'KSampler':
                workflow[node_id]['inputs']['steps'] = steps
        return workflow
    
    def _apply_cfg_scale(self, workflow: Dict, cfg: float) -> Dict:
        """Find and apply CFG scale to KSampler nodes."""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') == 'KSampler':
                workflow[node_id]['inputs']['cfg'] = cfg
        return workflow
    
    def _apply_custom_inputs(self, workflow: Dict, custom_inputs: Dict[str, Any]) -> Dict:
        """Apply custom input modifications to specific nodes.
        
        Args:
            workflow: The workflow dict
            custom_inputs: Dict mapping node_class_type -> {input_key: value}
                          e.g., {"CLIPTextEncode": {"text": "custom prompt"}}
                          or {"KSampler": {"seed": 12345}}
        """
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get('class_type') in custom_inputs:
                for input_key, input_value in custom_inputs[node_data['class_type']].items():
                    if input_key in node_data['inputs']:
                        node_data['inputs'][input_key] = input_value
        
        return workflow
    
    async def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for a prompt to finish and return history.
        
        Args:
            prompt_id: The prompt ID from .run()
            timeout: Maximum seconds to wait (default 5 min)
            
        Returns:
            History dict with outputs if completed, or status dict if timed out
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            history = await self.client.get_history(prompt_id)
            
            if prompt_id in history:
                return history[prompt_id]
            
            # Give it a moment
            await asyncio.sleep(2)
        
        # Timeout - check final status
        history = await self.client.get_history(prompt_id)
        return {
            'status': 'timeout',
            'prompt_id': prompt_id,
            'current_state': 'running or queued'
        }
    
    async def close(self):
        """Clean up resources."""
        await self.client.close()


async def main():
    """Example usage of WorkflowRunner."""
    
    # Initialize with your workflow JSON file
    runner = WorkflowRunner('your_workflow.json')
    
    try:
        # Single run with custom prompt
        result = await runner.run(
            prompt="a beautiful sunset over mountains",
            seed=42,  # Fixed seed for reproducibility
            steps=30,
            cfg_scale=7.5
        )
        
        print(f"Prompt ID: {result['prompt_id']}")
        
        # Wait for it to finish
        history = await runner.wait_for_completion(result['prompt_id'])
        print(f"Completion status: {history}")
        
    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
