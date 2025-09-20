"""Main entry point for the Suika Game."""

import sys
from pathlib import Path

import pyglet as pg

from suika.game import SuikaWindow


def main() -> None:
    """Main entry point for the Suika Game."""
    # Set up resource path for assets
    assets_path = Path(__file__).parent / "assets"
    pg.resource.path = [str(assets_path)]
    pg.resource.reindex()

    # Create and run the game
    try:
        window = SuikaWindow()
        pg.app.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running game: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
