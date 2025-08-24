import argparse
from pathlib import Path

# Default database path
DEFAULT_DB_PATH = Path("music_library.db")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ChipiChipi Music Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a directory for music')
    scan_parser.add_argument('directory', type=str, help='Path to the directory to scan')
    scan_parser.add_argument('--db', type=str, default="music_library.db", 
                           help='Path to the SQLite database file')
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help='Launch the graphical interface')
    gui_parser.add_argument('--db', type=str, default="music_library.db",
                          help='Path to the SQLite database file')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        from chipichipi.database import get_db_connection, init_db
        from chipichipi.scanner import scan_directory
        
        target_dir = Path(args.directory)
        db_path = Path(args.db)
        
        init_db(db_path)
        conn = get_db_connection(db_path)
        try:
            scan_directory(target_dir, conn)
            print(f"Scan complete! Database saved to: {db_path.absolute()}")
        finally:
            conn.close()
            
    elif args.command == 'gui':
        from chipichipi.app import main as gui_main
        gui_main()
        
    else:
        # If no command is provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()