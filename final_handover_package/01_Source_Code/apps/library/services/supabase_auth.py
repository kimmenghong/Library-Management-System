"""Supabase Auth integration helpers.

This service intentionally handles identity only. The lecturer-required
`users` table remains the source of truth for local profile data, role
assignment, and Django authorization.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SupabaseAuthError(Exception):
    """Base error raised for Supabase Auth failures."""

    def __init__(self, message, *, status_code=None, code="supabase_auth_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class SupabaseAuthConfigurationError(SupabaseAuthError, ImproperlyConfigured):
    """Raised when Supabase Auth is called before it is configured."""


@dataclass(frozen=True)
class SupabaseAuthIdentity:
    """Normalized identity/session data returned by Supabase Auth."""

    supabase_user_id: str
    email: str
    access_token: str = ""
    refresh_token: str = ""
    email_confirmed_at: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_session(self):
        return bool(self.access_token)


class SupabaseAuthService:
    """Small wrapper around Supabase Auth REST endpoints."""

    def __init__(self):
        self.enabled = bool(settings.USE_SUPABASE_AUTH)
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.timeout = settings.SUPABASE_AUTH_TIMEOUT

    def sign_up(self, *, email, password, metadata=None, email_redirect_to=None):
        """Create a Supabase Auth user with email/password credentials."""

        payload = {
            "email": self._clean_email(email),
            "password": password,
        }
        options = {}
        if metadata:
            options["data"] = metadata
        redirect_url = email_redirect_to or settings.SUPABASE_AUTH_REDIRECT_URL
        if redirect_url:
            options["email_redirect_to"] = redirect_url
        if options:
            payload["options"] = options

        data = self._request("POST", "signup", json=payload)
        return self._identity_from_payload(data)

    def sign_in_with_password(self, *, email, password):
        """Authenticate an existing Supabase Auth user by email/password."""

        data = self._request(
            "POST",
            "token",
            params={"grant_type": "password"},
            json={
                "email": self._clean_email(email),
                "password": password,
            },
        )
        return self._identity_from_payload(data)

    def refresh_session(self, *, refresh_token):
        """Exchange a refresh token for a new Supabase Auth session."""

        data = self._request(
            "POST",
            "token",
            params={"grant_type": "refresh_token"},
            json={"refresh_token": refresh_token},
        )
        return self._identity_from_payload(data)

    def get_user(self, *, access_token):
        """Retrieve the Supabase Auth user for a verified access token."""

        data = self._request("GET", "user", access_token=access_token)
        return self._identity_from_payload({"user": data})

    def sign_out(self, *, access_token):
        """Invalidate a Supabase Auth access token when possible."""

        self._request("POST", "logout", access_token=access_token)

    def _request(self, method, path, *, json=None, params=None, access_token=None):
        self._ensure_configured()
        url = f"{self.base_url}/auth/v1/{path.lstrip('/')}"
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise SupabaseAuthError(
                "Unable to reach Supabase Auth. Check your network and Supabase URL.",
                code="supabase_auth_unreachable",
            ) from exc

        if response.status_code >= 400:
            raise self._error_from_response(response)
        if not response.content:
            return {}
        return response.json()

    def _ensure_configured(self):
        if not self.enabled:
            raise SupabaseAuthConfigurationError(
                "Supabase Auth is disabled. Set USE_SUPABASE_AUTH=True to enable it.",
                code="supabase_auth_disabled",
            )
        if not self.base_url or not self.anon_key:
            raise SupabaseAuthConfigurationError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be configured.",
                code="supabase_auth_missing_settings",
            )

    def _error_from_response(self, response):
        message = "Supabase Auth request failed."
        code = "supabase_auth_request_failed"
        try:
            data = response.json()
        except ValueError:
            data = {}

        for key in ("msg", "message", "error_description", "error"):
            value = data.get(key)
            if value:
                message = str(value)
                break
        if data.get("code"):
            code = str(data["code"])
        elif data.get("error_code"):
            code = str(data["error_code"])

        return SupabaseAuthError(
            message,
            status_code=response.status_code,
            code=code,
        )

    def _identity_from_payload(self, payload):
        user = payload.get("user") or payload
        session = payload.get("session") or payload

        supabase_user_id = str(user.get("id") or "")
        email = self._clean_email(user.get("email") or "")
        if not supabase_user_id or not email:
            raise SupabaseAuthError(
                "Supabase Auth response did not include a valid user ID and email.",
                code="supabase_auth_invalid_response",
            )

        return SupabaseAuthIdentity(
            supabase_user_id=supabase_user_id,
            email=email,
            access_token=session.get("access_token") or "",
            refresh_token=session.get("refresh_token") or "",
            email_confirmed_at=user.get("email_confirmed_at") or "",
            raw=payload,
        )

    def _clean_email(self, email):
        return str(email or "").strip().lower()


def get_supabase_auth_service():
    """Return a fresh Supabase Auth service instance."""

    return SupabaseAuthService()
