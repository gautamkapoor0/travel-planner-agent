"""
conftest.py — pytest configuration.
Adds the project root to sys.path so `src.*` imports work correctly.
"""
import sys
import os

# Ensure the project root is on sys.path when running pytest from any directory
sys.path.insert(0, os.path.dirname(__file__))
