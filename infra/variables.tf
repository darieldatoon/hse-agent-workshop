variable "attendees_csv" {
  description = "CSV with an email column; other columns are ignored. Gitignored: it holds real people."
  type        = string
  default     = "attendees.csv"
}

variable "spare_workspaces" {
  description = "Extra workspaces for walk-ins, handed out on the day."
  type        = number
  default     = 5
}

variable "openai_api_key" {
  description = "OpenAI key stored in every workspace for the gateway. The infra tasks pass OPENAI_API_KEY from ../.env."
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.openai_api_key)) > 0
    error_message = "Set OPENAI_API_KEY in .env; an empty key would be stored in every workspace."
  }
}
