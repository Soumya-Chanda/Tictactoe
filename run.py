"""
TicTacMaster — Entry Point
Run this file to start the web application.

Usage:
    python run.py               # Development server (debug mode)
    python run.py --prod        # Production-like (no debug)

Then open: http://localhost:5000
"""
import sys
import os

# Make sure imports work from the project root
sys.path.insert(0, os.path.dirname(__file__))

from database.models import init_db

def main():
    prod = '--prod' in sys.argv

    print("=" * 50)
    print("  ✕○  TicTacMaster")
    print("=" * 50)
    print()
    print("  Initializing database...")
    init_db()
    print("  Database ready ✓")
    print()
    print(f"  Mode: {'Production' if prod else 'Development'}")
    print(f"  URL:  http://localhost:5000")
    print()
    print("  Press CTRL+C to stop")
    print("=" * 50)

    from app import app
    app.run(
        debug=not prod,
        host='0.0.0.0',
        port=5000,
        use_reloader=not prod,
    )

if __name__ == '__main__':
    main()
