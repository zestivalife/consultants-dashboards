export function buildInvitationMessage({ clientName, practiceName, shareUrl }) {
  return `Hi ${clientName},\n\nI've invited you to complete your health profile before our consultation.\n\nPlease use the secure link below:\n\n${shareUrl}\n\nRegards,\n${practiceName}`;
}

export function buildWhatsAppInvitationUrl(input) {
  return `https://wa.me/?text=${encodeURIComponent(buildInvitationMessage(input))}`;
}

export function buildEmailInvitationUrl(input) {
  const subject = `Health Profile Invitation from ${input.practiceName}`;
  return `mailto:${encodeURIComponent(input.email || '')}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(buildInvitationMessage(input))}`;
}
