from pathlib import Path
import ajishio as aj

project_dir: Path = Path(__file__).parent
sprites: dict[str, aj.GameSprite] = aj.load_aseprite_sprites(project_dir / 'sprites')
rooms: list[aj.GameLevel] = aj.load_ldtk_levels(project_dir / "room_data" / "level" / "simplified")