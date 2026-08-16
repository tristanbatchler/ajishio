import ajishio as aj


def draw_wrapped_text(
    x: float,
    y: float,
    text: str,
    color: aj.Color,
    *,
    max_width: float = 0.0,
    line_height: float = 24.0,
) -> int:
    """Draw text wrapped to max_width. Returns number of lines drawn."""
    effective_max = max_width if max_width > 0 else aj.room_width - x - 20
    if effective_max <= 0:
        effective_max = aj.room_width - x - 20
    words = text.split()
    if not words:
        return 0
    lines: list[str] = []
    current_line: list[str] = []
    current_width: float = 0.0
    for word in words:
        word_w = aj.text_width(word) + aj.text_width(" ")
        if current_width + word_w > effective_max and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_w
        else:
            current_line.append(word)
            current_width += word_w
    if current_line:
        lines.append(" ".join(current_line))
    for i, line_text in enumerate(lines):
        aj.draw_text(x, y + i * line_height, line_text, color)
    return len(lines)
