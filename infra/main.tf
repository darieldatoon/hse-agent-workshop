locals {
  attendees = { for a in csvdecode(file(var.attendees_csv)) : lower(trimspace(a.email)) => a }
  spares    = { for i in range(var.spare_workspaces) : format("spare-%02d", i + 1) => format("Spare %02d", i + 1) }

  # The email's local part, letters and digits only: jackie.smith@example.com -> jackiesmith.
  workspace_names = { for email in keys(local.attendees) : email => replace(split("@", email)[0], "/[^a-z0-9]/", "") }

  workspace_ids = merge(
    { for email, w in langsmith_workspace.attendee : email => w.id },
    { for key, w in langsmith_workspace.spare : key => w.id },
  )

  # What the lab writes, on top of what a Viewer can read. Keep deletes and sharing out: attendees
  # must not be able to wipe the seeded traces or publish workshop data.
  attendee_writes = [
    "gateway:invoke",          # model calls in every notebook; Admin is the only built-in role with it
    "runs:create",             # tracing
    "projects:create",         # tracing projects and experiments
    "projects:update",         # experiments record their end when they finish
    "feedback:create",         # the hunt's flag, and evaluator scores
    "feedback:update",         # fixing a flag
    "feedback-configs:create", # the first score under a new evaluator key
    "datasets:create",         # Add to Dataset in 03
    "datasets:update",
    "experiments:run",
  ]
}

data "langsmith_org_role" "user" {
  name = "ORGANIZATION_USER"
}

data "langsmith_workspace_role" "viewer" {
  name = "WORKSPACE_VIEWER"
}

# Viewer's reads keep every page in the UI working; the writes are only what the lab uses.
resource "langsmith_workspace_role" "attendee" {
  display_name = "Workshop Attendee"
  description  = "Everything a Viewer can see, plus what the lab writes: traces, feedback, datasets, experiments and model calls through the gateway. No deletes, sharing or workspace settings."
  permissions  = sort(distinct(concat(data.langsmith_workspace_role.viewer.permissions, local.attendee_writes)))
}

# One workspace per attendee, named so they can pick it out in the workspace switcher.
resource "langsmith_workspace" "attendee" {
  for_each     = local.attendees
  display_name = local.workspace_names[each.key]

  lifecycle {
    precondition {
      condition     = length(distinct(values(local.workspace_names))) == length(local.workspace_names)
      error_message = "Two attendee emails share a local part, so their workspaces would share a name."
    }
  }
}

resource "langsmith_workspace" "spare" {
  for_each     = local.spares
  display_name = each.value
}
