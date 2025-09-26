#!/usr/bin/env python3
"""
ASCII Starburst Generator (horizontal, symmetric, width-aligned)

Fix:
- Per-line gap is computed so each row's total width matches the middle line.
  This guarantees mirrored spacing on both sides (no "drifting" gaps).

Features:
- Odd number of branches per side (3, 5, 7, ...)
- Straight middle line; angled branches above/below
- Mirrored left/right with matching --- connectors
- Custom labels for left/right and center
- Tunable dash lengths
- Optional save-to-file
"""

from typing import List, Optional


def starburst(n_per_side: int,
              center_label: str = "Center",
              left_labels: Optional[List[str]] = None,
              right_labels: Optional[List[str]] = None,
              mid_dash_len: int = 13,
              first_dash_len: int = 3,
              dash_step: int = 2) -> str:
    """
    Build a horizontal starburst.

    n_per_side     : odd number of branches per side (>=1)
    center_label   : text inside [Center]
    left_labels    : top-to-bottom labels for L1..LN (defaults to L1..LN)
    right_labels   : top-to-bottom labels for R1..RN (defaults to R1..RN)
    mid_dash_len   : number of '-' on each side of [Center] for the middle line
    first_dash_len : dash length for the *outermost* angled lines (default 3)
    dash_step      : increase in dashes as you move inward (default +2)

    Spacing rule:
    For every non-middle row, we set:
        gap = len(middle_line) - len(left_part) - len(right_part)
    ensuring exact symmetry per line.
    """
    if n_per_side < 1 or n_per_side % 2 == 0:
        raise ValueError("n_per_side must be an odd integer >= 1, e.g. 3, 5, 7.")

    # Default labels
    if left_labels is None:
        left_labels = [f"L{i}" for i in range(1, n_per_side + 1)]
    if right_labels is None:
        right_labels = [f"R{i}" for i in range(1, n_per_side + 1)]

    if len(left_labels) != n_per_side or len(right_labels) != n_per_side:
        raise ValueError("left_labels and right_labels must each have length n_per_side.")

    def L(i): return f"[{left_labels[i-1]}]"
    def R(i): return f"[{right_labels[i-1]}]"
    center = f"[{center_label}]"

    mid = (n_per_side + 1) // 2  # which index is the straight spine

    # Build the middle line (defines target total width for all rows)
    mid_left = f"{L(mid)} {'-'*mid_dash_len}"
    mid_right = f"{'-'*mid_dash_len} {R(mid)}"
    middle_line = f"{mid_left} {center} {mid_right}"
    target_width = len(middle_line)

    # Dash lengths for angled rows: grow towards the middle (outer -> inner)
    # For example with first=3, step=2 and mid=3 (N=5): [3, 5]
    dash_seq = [first_dash_len + dash_step * i for i in range(0, mid - 1)]

    lines = []

    # Upper angled lines (top to just above middle)
    # i goes 1..mid-1 (top to just above center); dash_len increases inward
    for i in range(1, mid):
        dash_len = dash_seq[i - 1]
        left_part = f"{L(i)} {'-'*dash_len}\\"
        right_part = f"/{'-'*dash_len} {R(i)}"
        gap = max(1, target_width - len(left_part) - len(right_part))
        lines.append(left_part + (" " * gap) + right_part)

    # Middle straight line (spine)
    lines.append(middle_line)

    # Lower angled lines (just below middle to bottom)
    # Mirror the dash lengths outward again: inner -> outer (reverse of upper)
    for j, i in enumerate(range(mid + 1, n_per_side + 1), start=1):
        dash_len = dash_seq[-j]  # mirror
        left_part = f"{L(i)} {'-'*dash_len}/"
        right_part = f"\\{'-'*dash_len} {R(i)}"
        gap = max(1, target_width - len(left_part) - len(right_part))
        lines.append(left_part + (" " * gap) + right_part)

    return "\n".join(lines)


def main():
    print("ASCII Starburst Generator")
    print("=========================")
    try:
        n = int(input("Enter an odd number of branches per side (e.g., 3, 5, 7): ").strip())
        center = input("Center label [default: Center]: ").strip() or "Center"

        use_custom = input("Custom branch labels? (y/n): ").strip().lower() == "y"
        if use_custom:
            print(f"\nEnter {n} LEFT labels (top to bottom). Leave blank to use defaults.")
            left_labels = [input(f"L{i+1}: ").strip() or f"L{i+1}" for i in range(n)]
            print(f"\nEnter {n} RIGHT labels (top to bottom). Leave blank to use defaults.")
            right_labels = [input(f"R{i+1}: ").strip() or f"R{i+1}" for i in range(n)]
        else:
            left_labels = right_labels = None

        # Optional tweaks
        mid_dash_len = input("Middle dash length per side [default: 13]: ").strip()
        mid_dash_len = int(mid_dash_len) if mid_dash_len else 13

        first_dash_len = input("Outermost angled dash length [default: 3]: ").strip()
        first_dash_len = int(first_dash_len) if first_dash_len else 3

        dash_step = input("Dash growth step (toward center) [default: 2]: ").strip()
        dash_step = int(dash_step) if dash_step else 2

        diagram = starburst(
            n_per_side=n,
            center_label=center,
            left_labels=left_labels,
            right_labels=right_labels,
            mid_dash_len=mid_dash_len,
            first_dash_len=first_dash_len,
            dash_step=dash_step
        )

        print("\nGenerated Starburst:\n")
        print(diagram)

        save = input("\nSave to file? (y/n): ").strip().lower()
        if save == "y":
            path = input("Filename (e.g., starburst.txt): ").strip() or "starburst.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(diagram + "\n")
            print(f"Saved to {path}")

    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
