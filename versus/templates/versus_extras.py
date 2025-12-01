from django import template

register = template.Library()

SPORT_IMAGE_MAP = {
    "sepak bola": "images/sports/soccer.png",
    "futsal": "images/sports/futsal.png",
    "basket": "images/sports/basketball.png",
    "basketball": "images/sports/basketball.png",
    "badminton": "images/sports/badminton.png",
    "voli": "images/sports/volleyball.png",
    "volleyball": "images/sports/volleyball.png",
    "tenis": "images/sports/tennis.png",
}

@register.simple_tag
def sport_image(sport_name: str | None):
    key = (sport_name or "").strip().lower()
    return SPORT_IMAGE_MAP.get(key, "images/sports/default.png")
