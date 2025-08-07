def build_fancy_diagram(
    left_side: list[str],
    main_pre_evo: str,
    current: str,
    main_line: str,
    right_side: list[str]
) -> str:
    """
    Dynamically builds the ASCII diagram:

          left_top[0] ──┐               ┌── right_top[0]
                        │               │
    left_top[1]   ──┐   │               │   ┌── right_top[1]
                    │   │               │   │
    main_pre_evo ═══╪═══╪═══ current ═══╪═══╪═══ main_line
                    │   │               │   │
    left_bottom[0]  ──┘   │             │   └── right_bottom[0]
                        │               │
          left_bottom[1] ──┘           └── right_bottom[1]

    - We split `left_side` into top/bottom halves, similarly `right_side`.
    - The center row has main_pre_evo ═╪══ current ═╪══ main_line with bridging '┐', '┘', etc.
    - 'Top' lines are placed above the center, 'bottom' lines below.

    Spacing can be tweaked to accommodate longer or shorter names.
    """
    import math

    # 1) Split left_side into top/bottom
    n_left = len(left_side)
    top_left_count = n_left // 2  # half for top
    bottom_left_count = n_left - top_left_count
    left_top = left_side[:top_left_count]
    left_bottom = left_side[top_left_count:]

    # 2) Split right_side into top/bottom
    n_right = len(right_side)
    top_right_count = n_right // 2
    bottom_right_count = n_right - top_right_count
    right_top = right_side[:top_right_count]
    right_bottom = right_side[top_right_count:]

    lines = []

    # Adjust these spacing constants if needed:
    indent_left = 6    # how far the top lines are indented from the left margin
    gap_between = 14   # horizontal gap between left portion and right portion
    center_line_spacing = 2  # minimal spacing around the center line parts

    # We'll define a small helper for building a line with left text + right text
    def build_line(left_text: str, right_text: str) -> str:
        # The left_text is placed directly, the right_text is placed gap_between spaces away
        gap = " " * gap_between
        return left_text + gap + right_text

    # ─────────────────────────────────────────────────────────────────────────────
    # 3) Print the TOP half (above the center line)

    # We'll iterate row by row up to max(top_left_count, top_right_count)
    top_count = max(top_left_count, top_right_count)

    for i in range(top_count):
        # LHS
        if i < len(left_top):
            # E.g. "      SideLine ──┐"
            left_str = f"{' ' * indent_left}{left_top[i]:<10}──┐"
        else:
            # No line here, just blank with enough spacing
            left_str = " " * (indent_left + 12)

        # RHS
        if i < len(right_top):
            # E.g. "┌── SideLine"
            right_str = f"┌── {right_top[i]}"
        else:
            right_str = ""

        # Combine
        line = build_line(left_str, right_str)
        lines.append(line)

        # Next line for vertical connectors (unless it's the last row)
        if i < top_count - 1:
            # We still have more top lines
            left_conn = " " * (indent_left + 12) + "│"
            right_conn = "│" if (i < len(right_top)) else ""
            lines.append(build_line(left_conn, right_conn))
        else:
            # The last top line: connect down to center row
            left_conn = " " * (indent_left + 12) + "│"
            right_conn = "│" if (i < len(right_top)) else ""
            lines.append(build_line(left_conn, right_conn))

    # ─────────────────────────────────────────────────────────────────────────────
    # 4) The CENTER ROW
    #
    # "main_pre_evo ═══╪═══ current ═══╪═══ main_line"
    # We'll place them in one line with spacing in between.
    center_parts = [
        main_pre_evo, 
        "═══╪═══",  # bridging
        current, 
        "═══╪═══", 
        main_line
    ]
    center_line = " ".join(center_parts)
    # Indent it so it lines under the "│" from the left side. That means we do at least `indent_left` spaces.
    center_line = " " * indent_left + center_line
    lines.append(center_line)

    # ─────────────────────────────────────────────────────────────────────────────
    # 5) The connector line under the center (only if there are bottom lines)
    if bottom_left_count > 0 or bottom_right_count > 0:
        # We want a line with "   │   │" under the '╪' or so. We can do a small trick:
        # We'll find indices of '╪' in the center_line and put '│' under them.
        center_chars = list(center_line)
        indices = [i for i, ch in enumerate(center_chars) if ch == '╪']
        connector = [" "] * len(center_line)
        for ix in indices:
            connector[ix] = "│"
        lines.append("".join(connector))

    # ─────────────────────────────────────────────────────────────────────────────
    # 6) Print the BOTTOM half
    bottom_count = max(bottom_left_count, bottom_right_count)

    for i in range(bottom_count):
        # LHS
        if i < len(left_bottom):
            # e.g. "  SideLine ──┘"
            left_str = f"{' ' * indent_left}{left_bottom[i]:<10}──┘"
        else:
            left_str = " " * (indent_left + 12)

        # RHS
        if i < len(right_bottom):
            right_str = f"└── {right_bottom[i]}"
        else:
            right_str = ""

        line = build_line(left_str, right_str)
        lines.append(line)

        # Another line for vertical connectors (unless it's the last row)
        if i < bottom_count - 1:
            left_conn = " " * (indent_left + 12) + "│"
            right_conn = "│" if (i < len(right_bottom)) else ""
            lines.append(build_line(left_conn, right_conn))

    # Finally, wrap the entire thing in a code block
    return "```\n" + "\n".join(lines) + "\n```"
