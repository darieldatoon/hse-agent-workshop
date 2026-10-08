output "workspaces" {
  description = "Workspace name and ID per attendee email, plus the spares."
  value = merge(
    { for email, w in langsmith_workspace.attendee : email => { name = w.display_name, id = w.id } },
    { for key, w in langsmith_workspace.spare : key => { name = w.display_name, id = w.id } },
  )
}

# Read by invite.py, which sends the org invites with each attendee's workspace attached.
output "attendee_role_id" {
  description = "Workspace role each attendee gets in their own workspace."
  value       = langsmith_workspace_role.attendee.id
}

output "org_user_role_id" {
  description = "Org role each attendee gets: enough to create a personal access token."
  value       = data.langsmith_org_role.user.id
}
