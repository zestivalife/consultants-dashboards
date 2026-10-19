"""P49 fixed, non-executable command vocabulary."""
COMMANDS={'OPEN_CLIENT','CREATE_APPOINTMENT','CREATE_INVOICE','CREATE_LEAD','OPEN_MARKETPLACE','OPEN_SUPPORT_TICKET','SHOW_TODAYS_APPOINTMENTS','SHOW_OVERDUE_INVOICES'}
def resolve_command(value):
 code=str(value).strip().upper().replace("'",'').replace(' ','_')
 if code not in COMMANDS:raise ValueError('Unknown safe command')
 return code
