"""P24 lead CRM invariants."""
STAGES=("NEW","CONTACTED","QUALIFIED","CONSULTATION_BOOKED","CONVERTED","NOT_INTERESTED","LOST")
TRANSITIONS={
 "NEW":{"CONTACTED","QUALIFIED","NOT_INTERESTED","LOST"},
 "CONTACTED":{"QUALIFIED","CONSULTATION_BOOKED","NOT_INTERESTED","LOST"},
 "QUALIFIED":{"CONTACTED","CONSULTATION_BOOKED","NOT_INTERESTED","LOST"},
 "CONSULTATION_BOOKED":{"QUALIFIED","CONVERTED","NOT_INTERESTED","LOST"},
 "NOT_INTERESTED":{"CONTACTED"},"LOST":{"CONTACTED"},"CONVERTED":set(),
}
def normal_email(value):return (value or "").strip().lower() or None
def normal_phone(value):
    digits="".join(character for character in (value or "") if character.isdigit())
    return digits or None
def assert_transition(current,target):
    if target not in TRANSITIONS.get(current,set()):raise ValueError("Lead stage transition is not permitted")
    return target
