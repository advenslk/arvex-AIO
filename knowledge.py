"""Editable ArveX facts used as trusted context before the AI answers."""

ARVEX_KNOWLEDGE = """
Brand: ArveX Hosting.
Website: https://www.arvex.host
The assistant must not invent current prices, plans, uptime, policies, staff names or availability. Add verified business facts here as they are confirmed.
When a fact is missing, ask the user to contact ArveX staff or say that the information is not currently configured.
""".strip()

def relevant_context(query: str) -> str:
    # Phase 1 keeps the trusted knowledge layer deliberately small.
    return ARVEX_KNOWLEDGE
