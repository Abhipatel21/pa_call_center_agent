import os
from jinja2 import Template

def load_prompt(template_name: str, **kwargs) -> str:
    """
    Loads a markdown prompt template from the prompts/ directory and renders it with Jinja2.
    """
    # Assuming prompts are in a 'prompts' directory at the project root
    # Adjust path logic as needed based on where this is run
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", template_name)
    
    if not prompt_path.endswith(".md"):
        prompt_path += ".md"
        
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = Template(template_content)
        return template.render(**kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found at {prompt_path}")
