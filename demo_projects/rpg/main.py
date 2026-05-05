import ajishio as aj
from pathlib import Path


def main():
    main_dir = Path(__file__).parent
    rooms = aj.load_ldtk_levels(
        main_dir / "rooms" / "world" / "simplified",
        cosmetic_layers={"FloorIntGrid"},
    )
    aj.set_rooms(rooms)
    aj.game_start()


if __name__ == "__main__":
    main()
