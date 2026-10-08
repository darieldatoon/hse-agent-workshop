variable "attendees_csv" {
  description = "CSV with first_name, last_name, email columns. Gitignored: it holds real people."
  type        = string
  default     = "attendees.csv"
}

variable "spare_workspaces" {
  description = "Extra workspaces for walk-ins, handed out on the day."
  type        = number
  default     = 5
}

variable "add_workspace_members" {
  description = <<-EOT
    Add each attendee to their own workspace. LangSmith only allows this once the attendee has
    accepted the org invite, so apply once with false, wait for invites to be accepted, then
    apply again with true.
  EOT
  type        = bool
  default     = false
}

variable "key_expires_at" {
  description = "When the shared workshop key stops working, RFC 3339 (e.g. 2026-10-14T23:59:59Z)."
  type        = string
}
