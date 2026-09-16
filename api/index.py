import os
import sys

# Add root directory to sys.path so app and submodules can be imported properly on Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import app
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export app for Vercel Serverless Function WSGI runner
__all__ = ['app']

