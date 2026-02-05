#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
purrrr Web Interface Launcher
Démarre l'interface web Flask de purrrr
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from purrrr.flask_app import run_flask_app

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Lance l'interface web purrrr",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python run_web.py                           # Lance sur 0.0.0.0:5000
  python run_web.py --host localhost          # Lance sur localhost:5000
  python run_web.py --port 8080               # Lance sur 0.0.0.0:8080
  python run_web.py --debug                   # Lance en mode debug
  python run_web.py --host localhost --port 8000 --debug
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Adresse IP de liaison (défaut: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port d'écoute (défaut: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug avec rechargement automatique"
    )
    
    args = parser.parse_args()
    
    
    print("=" * 50)
    print("purrrr WEB INTERFACE")
    print("Analyseur de Logs Microsoft Purview")
    print("=" * 50)
    print()
    print("Demarrage en cours...")
    print()
    print(f"Acces: http://0.0.0.0:{args.port}")
    print(f"Mode Debug: {'Actif' if args.debug else 'Desactive'}")
    print()
    print("Appuyez sur CTRL+C pour arreter le serveur")
    
    run_flask_app(host=args.host, port=args.port, debug=args.debug)
