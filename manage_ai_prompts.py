#!/usr/bin/env python3
"""
AI Prompts Management Script
This script provides an easy way to view, edit, and test AI prompts without touching the core code.
"""

import os
import sys
import json
from typing import Dict, Any

def load_prompts() -> Dict[str, Any]:
    """Load prompts from the configuration file"""
    try:
        from ai_prompts import PROMPT_TEMPLATES, MODEL_CONFIGS
        return {
            "prompts": PROMPT_TEMPLATES,
            "models": MODEL_CONFIGS
        }
    except ImportError as e:
        print(f"Error loading prompts: {e}")
        return {}

def display_prompts():
    """Display all current prompts in a readable format"""
    data = load_prompts()
    if not data:
        print("No prompts loaded.")
        return
    
    print("=" * 60)
    print("CURRENT AI PROMPTS CONFIGURATION")
    print("=" * 60)
    
    for prompt_type, template in data["prompts"].items():
        print(f"\n📝 {prompt_type.upper().replace('_', ' ')}")
        print("-" * 40)
        print(f"System Message:")
        print(template["system"][:200] + "..." if len(template["system"]) > 200 else template["system"])
        print(f"\nUser Template:")
        print(template["user_template"][:200] + "..." if len(template["user_template"]) > 200 else template["user_template"])
    
    print(f"\n🤖 MODEL CONFIGURATIONS")
    print("-" * 40)
    for model_name, config in data["models"].items():
        print(f"{model_name}: {config}")

def edit_prompt_interactive():
    """Interactive prompt editor"""
    data = load_prompts()
    if not data:
        print("No prompts loaded.")
        return
    
    print("\nAvailable prompt types:")
    for i, prompt_type in enumerate(data["prompts"].keys(), 1):
        print(f"{i}. {prompt_type}")
    
    try:
        choice = int(input("\nSelect prompt type to edit (number): ")) - 1
        prompt_types = list(data["prompts"].keys())
        if 0 <= choice < len(prompt_types):
            selected_type = prompt_types[choice]
            edit_single_prompt(selected_type, data["prompts"][selected_type])
        else:
            print("Invalid selection.")
    except (ValueError, IndexError):
        print("Invalid input.")

def edit_single_prompt(prompt_type: str, template: Dict[str, str]):
    """Edit a single prompt template"""
    print(f"\nEditing {prompt_type} prompt:")
    print("=" * 50)
    
    print(f"\nCurrent System Message:")
    print(template["system"])
    
    print(f"\nCurrent User Template:")
    print(template["user_template"])
    
    print(f"\nOptions:")
    print("1. Edit system message")
    print("2. Edit user template")
    print("3. View full prompts")
    print("4. Back to main menu")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        new_system = input("\nEnter new system message (or press Enter to keep current):\n").strip()
        if new_system:
            template["system"] = new_system
            print("System message updated!")
    
    elif choice == "2":
        new_template = input("\nEnter new user template (or press Enter to keep current):\n").strip()
        if new_template:
            template["user_template"] = new_template
            print("User template updated!")
    
    elif choice == "3":
        print(f"\nFull System Message:")
        print("-" * 30)
        print(template["system"])
        print(f"\nFull User Template:")
        print("-" * 30)
        print(template["user_template"])
    
    elif choice == "4":
        return
    
    else:
        print("Invalid option.")

def test_prompt():
    """Test a prompt with sample content"""
    data = load_prompts()
    if not data:
        print("No prompts loaded.")
        return
    
    print("\nAvailable prompt types for testing:")
    for i, prompt_type in enumerate(data["prompts"].keys(), 1):
        print(f"{i}. {prompt_type}")
    
    try:
        choice = int(input("\nSelect prompt type to test (number): ")) - 1
        prompt_types = list(data["prompts"].keys())
        if 0 <= choice < len(prompt_types):
            selected_type = prompt_types[choice]
            template = data["prompts"][selected_type]
            
            print(f"\nTesting {selected_type} prompt:")
            print("=" * 50)
            
            # Sample content for testing
            sample_content = input("Enter sample content to test with (or press Enter for default): ").strip()
            if not sample_content:
                sample_content = "This is a sample article about government policy changes affecting healthcare funding."
            
            # Format the prompt
            if selected_type == "article_summary":
                formatted_prompt = template["user_template"].format(
                    title="Test Article",
                    url="https://example.com/test-article",
                    content=sample_content
                )
            elif selected_type == "hansard_questions":
                formatted_prompt = template["user_template"].format(media_content=sample_content)
            else:
                formatted_prompt = template["user_template"]
            
            print(f"\nSystem Message:")
            print("-" * 30)
            print(template["system"])
            
            print(f"\nFormatted User Prompt:")
            print("-" * 30)
            print(formatted_prompt)
            
        else:
            print("Invalid selection.")
    except (ValueError, IndexError):
        print("Invalid input.")

def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 60)
        print("AI PROMPTS MANAGEMENT TOOL")
        print("=" * 60)
        print("1. View current prompts")
        print("2. Edit prompts interactively")
        print("3. Test prompts with sample content")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            display_prompts()
        elif choice == "2":
            edit_prompt_interactive()
        elif choice == "3":
            test_prompt()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
