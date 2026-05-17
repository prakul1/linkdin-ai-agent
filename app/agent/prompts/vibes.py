"""Vibe (tone) definitions — translated into prompt fragments."""
VIBE_DESCRIPTIONS = {
    "funny": "Inject light humor, wordplay, or self-deprecating jokes. Make readers smile but stay professional.",
    "serious": "Grounded, no-nonsense tone. Direct statements, no humor, focus on substance.",
    "motivational": "Energetic and inspiring. Use powerful verbs, paint a vision, end with an empowering call-to-action.",
    "witty": "Clever observations, sharp insights, a touch of irony. Smart but never condescending.",
    "casual": "Conversational and friendly, like talking to a colleague over coffee. Contractions OK, relaxed flow.",
    "professional": "Polished business tone. Industry-appropriate vocabulary, formal but not stiff.",
    "insightful": "Deep, analytical. Connect dots that others miss, share an original perspective.",
    "emotional": "Heartfelt and vulnerable. Share genuine feelings, lean into the human side of the story.",
    "celebratory": "Excited, gratitude-focused. Acknowledge wins, thank people involved, share the joy.",
    "auto": "Choose the most fitting tone based on the topic. Use your best judgment.",
}
def build_vibe_instruction(vibes: list[str]) -> str:
    """Combine selected vibes into a single instruction block."""
    if not vibes:
        return ""
    # If 'auto' is among them and it's the only one, let LLM decide
    if vibes == ["auto"]:
        return "TONE: Auto-detect based on the topic. Use your best judgment for the appropriate vibe."
    # If 'auto' is combined with others, ignore 'auto'
    active_vibes = [v for v in vibes if v != "auto"]
    if not active_vibes:
        return "TONE: Auto-detect based on the topic."
    if len(active_vibes) == 1:
        v = active_vibes[0]
        return f"TONE: {v.title()}\n{VIBE_DESCRIPTIONS[v]}"
    # Multiple vibes — blend them
    lines = [f"TONE: Blend of {' + '.join(v.title() for v in active_vibes)}"]
    lines.append("Combine these qualities:")
    for v in active_vibes:
        lines.append(f"- {v.title()}: {VIBE_DESCRIPTIONS[v]}")
    return "\n".join(lines)