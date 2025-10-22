#!/usr/bin/env python3
"""
Django-like app generator for the plugins directory.
Usage: python manage.py startapp <app_name>
"""
import os
import sys
import argparse
from pathlib import Path


def create_app(app_name):
    """Create a new app with Django-like structure under plugins directory."""
    
    # Validate app name
    if not app_name.isidentifier():
        print(f"Error: '{app_name}' is not a valid Python identifier.")
        return False
    
    # Create app directory structure
    plugins_dir = Path("plugins")
    app_dir = plugins_dir / app_name
    
    # Check if app already exists
    if app_dir.exists():
        print(f"Error: App '{app_name}' already exists in plugins directory.")
        return False
    
    # Create directories
    directories = [
        app_dir,
        app_dir / "views",
        app_dir / "utils",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create files with templates
    files_to_create = {
        app_dir / "models.py": get_models_template(app_name),
        app_dir / "views" / "__init__.py": get_views_init_template(),
        app_dir / "utils" / "__init__.py": get_utils_init_template(),
        app_dir / "utils" / "helpers.py": get_helpers_template(app_name),
    }
    
    # Create files
    for file_path, content in files_to_create.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created file: {file_path}")
    
    print(f"\nSuccessfully created app '{app_name}' in plugins directory!")
    print(f"\nApp structure:")
    print(f"plugins/{app_name}/")
    print(f"├── models.py")
    print(f"├── utils/")
    print(f"│   ├── __init__.py")
    print(f"│   └── helpers.py")
    print(f"└── views/")
    print(f"    └── __init__.py")
    
    return True


def get_models_template(app_name):
    """Get the template for models.py file."""
    return f'''from beanie import Document
from pydantic import Field
from datetime import datetime

# Example:
# class {app_name.capitalize()}Model(Document):
#     """Base model for {app_name} app."""
#     id: int = Field(alias="_id")
#     created_at: datetime = Field(default_factory=datetime.now)
#     updated_at: datetime = Field(default_factory=datetime.now)
# 
#     class Settings:
#         name = "{app_name}_collection"
'''


def get_views_init_template():
    """Get the template for views/__init__.py file."""
    return '''"""
Views package for the app.
Import your view modules here.
"""
'''


def get_utils_init_template():
    """Get the template for utils/__init__.py file."""
    return '''"""
Utilities package for the app.
"""
'''


def get_helpers_template(app_name):
    """Get the template for utils/helpers.py file."""
    return f'''
'''


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Django-like app generator for plugins directory",
        prog="manage.py"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # startapp command
    startapp_parser = subparsers.add_parser('startapp', help='Create a new app')
    startapp_parser.add_argument('app_name', help='Name of the app to create')
    
    # Parse arguments
    if len(sys.argv) < 2:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if args.command == 'startapp':
        if not args.app_name:
            print("Error: App name is required.")
            return
        
        success = create_app(args.app_name)
        if success:
            print(f"\nNext steps:")
            print(f"1. Add your views in plugins/{args.app_name}/views/")
            print(f"2. Update the models in plugins/{args.app_name}/models.py")
            print(f"3. Add utility functions in plugins/{args.app_name}/utils/helpers.py")
            print(f"4. Import your views in your main application")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()