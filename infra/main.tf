locals {
  attendees = { for a in csvdecode(file(var.attendees_csv)) : lower(trimspace(a.email)) => a }
  spares    = { for i in range(var.spare_workspaces) : format("spare-%02d", i + 1) => format("Spare %02d", i + 1) }
}

data "langsmith_org_role" "user" {
  name = "ORGANIZATION_USER"
}

data "langsmith_workspace_role" "admin" {
  name = "WORKSPACE_ADMIN"
}

# One workspace per attendee, named so they can pick it out in the workspace switcher.
resource "langsmith_workspace" "attendee" {
  for_each     = local.attendees
  display_name = "${trimspace(each.value.first_name)} ${trimspace(each.value.last_name)}"
}

resource "langsmith_workspace" "spare" {
  for_each     = local.spares
  display_name = each.value
}

resource "langsmith_org_membership" "attendee" {
  for_each = local.attendees
  email    = each.key
  role_id  = data.langsmith_org_role.user.id
}

# Each attendee joins only their own workspace, so nobody can browse someone else's findings.
resource "langsmith_workspace_membership" "attendee" {
  for_each     = var.add_workspace_members ? local.attendees : {}
  workspace_id = langsmith_workspace.attendee[each.key].id
  email        = each.key
  role_id      = data.langsmith_workspace_role.admin.id

  depends_on = [langsmith_org_membership.attendee]
}
