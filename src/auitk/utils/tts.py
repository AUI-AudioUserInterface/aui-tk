def map_star_hash(text: str) -> str:
    # sehr simpel; passe bei Bedarf regex-basiert an
    return text.replace("*", "Stern").replace("#", "Raute")
