# Auth-Gated App Testing Playbook (Rimpods Admin)

## Test Admin Whitelist
`backend/.env` key: `ADMIN_EMAILS` — comma separated allowlist.
Current: `admin@rimpods.test` (placeholder — update to real admin emails in prod).

## Step 1: Create Test Admin User & Session
```bash
mongosh "$MONGO_URL" --eval "
use('$DB_NAME');
var userId = 'user_test' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'admin@rimpods.test',
  name: 'Rimpods Admin',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```bash
# Should return admin user data
curl -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Admin-protected endpoints
curl -X GET "$API_URL/api/admin/orders" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

curl -X GET "$API_URL/api/admin/stats" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Non-admin email session should get 403 on /api/admin/*
```

## Step 3: Browser Testing
```python
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "coral-product-hub.preview.emergentagent.com",
    "path": "/",
    "httpOnly": True,
    "secure": True,
    "sameSite": "None"
}])
await page.goto("https://coral-product-hub.preview.emergentagent.com/admin")
```

## Quick Cleanup
```bash
mongosh "$MONGO_URL" --eval "
use('$DB_NAME');
db.users.deleteMany({email: 'admin@rimpods.test'});
db.user_sessions.deleteMany({session_token: /test_session/});
"
```

## Checklist
- [ ] Session has `user_id` matching users.user_id
- [ ] All user/session queries use `{_id:0}` projection
- [ ] `/api/auth/me` returns 200 with user object for admin email
- [ ] `/api/admin/*` returns 403 for non-whitelisted email, 200 for whitelisted
- [ ] `/admin` React route redirects to Emergent Auth if no cookie
- [ ] Logout clears cookie + deletes session row
