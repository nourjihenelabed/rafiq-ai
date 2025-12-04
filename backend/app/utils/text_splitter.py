def naive_chunker(text: str, max_chars: int = 800):
    """
    Very small chunker: splits on sentences-ish boundaries up to max_chars.
    """
    if len(text) <= max_chars:
        return [text]
    pieces = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            pieces.append(text[start:].strip())
            break
        # try to break at the last period within range
        slice_ = text[start:end]
        last_dot = slice_.rfind(".")
        if last_dot != -1 and last_dot > max_chars // 3:
            pieces.append(slice_[:last_dot+1].strip())
            start = start + last_dot + 1
        else:
            pieces.append(slice_.strip())
            start = end
    return pieces
