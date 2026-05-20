import contextlib

import typing_extensions as tp

__all__ = ("TextLines",)


class TextLines:
    """Object to manage (possibly) indented strings."""

    def __init__(self, *, spacer: str = "  "):
        self._lines: list[str] = []
        self._spacer = spacer
        self._indent_level = 0

    def append(self, line: str, /):
        self._lines.append(f"{self._spacer * self._indent_level}{line}")

    def extend(self, lines: tp.Iterable[str] | "TextLines", /):
        iterable = lines._lines if isinstance(lines, TextLines) else lines
        self._lines.extend((f"{self._spacer * self._indent_level}{line}" for line in iterable))

    @contextlib.contextmanager
    def indent(self, initial: str | None = None, /):
        """Indent text added with the context.

        Args:
            initial: Optional string to store _before_ indenting.
        """
        # setup
        if initial is not None:
            self.append(initial)
        self._indent_level += 1
        try:
            yield
        finally:
            self._indent_level -= 1

    def export(self, sep: str = "\n") -> str:
        """Export this class as a block of text."""
        return sep.join(self._lines)

    def __str__(self):
        return self.export()

    def __repr__(self):
        return f"<TextLines with {len(self)} lines of text>"

    def __len__(self):
        return len(self._lines)

    def __bool__(self):
        return bool(self._lines)
