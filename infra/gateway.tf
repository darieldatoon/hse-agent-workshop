data "langsmith_org" "current" {}

# Every workspace calls OpenAI through the gateway with this key. Provider secrets are per
# workspace: one stored elsewhere does not reach these.
resource "langsmith_workspace_secret" "openai" {
  for_each     = local.workspace_ids
  workspace_id = each.value
  key          = "OPENAI_API_KEY"
  value        = var.openai_api_key
}

# Spend caps. Every matching policy is enforced, so a request counts against the org, its
# workspace and its user at once, and any one of them can block it.
resource "langsmith_gateway_policy" "org_monthly" {
  name             = "Workshop org: $500 per month"
  action           = "block"
  subject_matchers = [{ key = "organization_id", value = data.langsmith_org.current.id }]
  config = {
    spend_cap = { limit_usd = 500, window = "monthly" }
  }
}

resource "langsmith_gateway_policy" "per_workspace_daily" {
  name             = "Each workspace: $50 per day"
  action           = "block"
  subject_matchers = [{ key = "workspace_id", value = "" }]
  config = {
    default_spend_cap = { limit_usd = 50, window = "daily" }
  }
}

resource "langsmith_gateway_policy" "per_user_daily" {
  name             = "Each user: $50 per day"
  action           = "block"
  subject_matchers = [{ key = "user_id", value = "" }]
  config = {
    default_spend_cap = { limit_usd = 50, window = "daily" }
  }
}
