"""LinkedIn API constants — URLs, scopes, OAuth endpoints."""
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE = "https://api.linkedin.com"
USERINFO_URL = f"{LINKEDIN_API_BASE}/v2/userinfo"
UGC_POSTS_URL = f"{LINKEDIN_API_BASE}/v2/ugcPosts"
ASSETS_REGISTER_URL = f"{LINKEDIN_API_BASE}/v2/assets?action=registerUpload"
DEFAULT_SCOPES = ["openid", "profile", "email", "w_member_social"]
LINKEDIN_VERSION = "202405"