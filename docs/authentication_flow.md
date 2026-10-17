# Supabase Email OTP Authentication Architecture

## 1. End-to-End Authentication Flow

The application implements a passwordless **Email OTP (One-Time Password)** flow. The frontend handles code delivery and verification directly with Supabase Auth, while the FastAPI backend verifies the resulting JWT session token on every API call.

```
┌──────────┐                 ┌───────────────┐              ┌────────────────┐              ┌───────────────┐
│ User     │                 │ React Client  │              │ Supabase Auth  │              │ FastAPI Backend│
│ (Browser)│                 │ (supabase-js) │              │  (Cloud API)   │              │  (Python API) │
└────┬─────┘                 └───────┬───────┘              └───────┬────────┘              └───────┬───────┘
     │                               │                              │                               │
     │ 1. Enters email               │                              │                               │
     ├──────────────────────────────>│                              │                               │
     │                               │ 2. signInWithOtp({ email })  │                               │
     │                               ├─────────────────────────────>│                               │
     │                               │                              │ 3. Sends OTP code via email   │
     │                               │                              ├──────────────────────────────>│ (to user inbox)
     │ 4. Enters 6-digit OTP code    │                              │                               │
     ├──────────────────────────────>│                              │                               │
     │                               │ 5. verifyOtp({ email, token})│                               │
     │                               ├─────────────────────────────>│                               │
     │                               │ 6. Returns Session (JWT)     │                               │
     │                               │<─────────────────────────────┤                               │
     │                               │                              │                               │
     │                               │ 7. API Request with Header:  │                               │
     │                               │    Authorization: Bearer <JWT>                               │
     │                               ├─────────────────────────────────────────────────────────────>│
     │                               │                              │                               │
     │                               │                              │ 8. GET /auth/v1/user          │
     │                               │                              │    (Checks token validity)    │
     │                               │                              │<──────────────────────────────┤
     │                               │                              │ 9. Returns user {id, email}   │
     │                               │                              ├──────────────────────────────>│
     │                               │                              │                               │ 10. Cache token for 60s
     │                               │                              │                               │ 11. Run service with
     │                               │                              │                               │     verified user_id
     │                               │ 12. Returns JSON Response    │                               │
     │                               │<─────────────────────────────────────────────────────────────┤
```

---

## 2. Why the Backend Never Touches OTP Codes or Passwords

1. **Zero Secret Handling:** The backend never stores user passwords, hashes, or OTP codes.
2. **Standard JWT Verification:** The backend functions purely as a resource server. It validates the Bearer token against Supabase Auth (`GET {SUPABASE_URL}/auth/v1/user`) using HTTP/2 asynchronous connection pooling.
3. **No Unsafe JWT Decoding:** The backend does NOT merely decode unverified JWT claims from base64; it ensures Supabase's cryptographic signature and user session active status are valid.
4. **Token Cache Performance:** Validated tokens are cached in memory for **60 seconds**, keyed by a SHA-256 hash of the token. This prevents latency bottlenecks while ensuring revoked tokens expire within 60 seconds.

---

## 3. Human-Only Supabase Dashboard Setup Checklist

You must manually verify the following settings in your Supabase Dashboard:

1. **Enable Email Provider:**
   - Go to **Authentication** -> **Providers** -> **Email**.
   - Ensure the toggle is **Enabled**.
   - Ensure **Confirm email** or **Enable Email OTP** is enabled.

2. **Email OTP Template:**
   - Go to **Authentication** -> **Email Templates** -> **Magic Link** or **Confirmation**.
   - Make sure `{{ .Token }}` is present in the email body so the 6-digit code is sent to the user:
     ```html
     <h2>Your confirmation code is:</h2>
     <p><strong>{{ .Token }}</strong></p>
     ```

3. **Rate Limits & SMTP (For Production):**
   - By default, Supabase's built-in email service allows ~3-4 emails per hour for testing.
   - For production, configure custom SMTP (e.g. Resend, SendGrid, Amazon SES) in **Project Settings** -> **Authentication** -> **SMTP Settings**.

4. **Redirect URLs:**
   - In **Authentication** -> **URL Configuration**, set Site URL to `http://localhost:5173` for development and your Vercel domain for production.
