output "workspaces" {
  description = "Workspace name and ID per attendee email, plus the spares."
  value = merge(
    { for email, w in langsmith_workspace.attendee : email => { name = w.display_name, id = w.id } },
    { for key, w in langsmith_workspace.spare : key => { name = w.display_name, id = w.id } },
  )
}

output "invite_status" {
  description = "Org invite status per attendee: pending until they accept."
  value       = { for email, m in langsmith_org_membership.attendee : email => m.status }
}
