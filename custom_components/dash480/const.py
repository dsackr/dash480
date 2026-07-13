"""Constants for the Dash480 integration."""

DOMAIN = "dash480"

# (label, HASP-font hex codepoint) icon choices, shared by the legacy
# per-slot icon select and the visual builder's dash480/registry/icons
# command so the two pickers can never drift apart.
ICON_CHOICES = [
    ("Power (E425)", "E425"),
    ("Fan (E210)", "E210"),
    ("Light (E335)", "E335"),
    ("Up (E143)", "E143"),
    ("Stop (E4DB)", "E4DB"),
    ("Down (E140)", "E140"),
    # Placeholder, unverified against the actual font on the device — correct
    # via this picker if it doesn't render as a calendar glyph.
    ("Calendar (E1C0)", "E1C0"),
]
