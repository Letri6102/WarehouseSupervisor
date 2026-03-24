import requests
from typing import List, Dict, Any, Optional


class ZaloOANotifier:
    def __init__(
        self,
        access_token: str,
        endpoint: str,
        recipients: Optional[List[str]] = None,
        enabled: bool = True,
        timeout: int = 15,
    ):
        self.access_token = (access_token or "").strip()
        self.endpoint = (endpoint or "").strip()
        self.recipients = [x.strip() for x in (recipients or []) if x and x.strip()]
        self.enabled = enabled
        self.timeout = timeout

    def is_ready(self) -> bool:
        return (
            self.enabled
            and bool(self.access_token)
            and bool(self.endpoint)
            and len(self.recipients) > 0
        )

    def send_text(self, user_id: str, text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "disabled"}

        if not self.access_token:
            return {"ok": False, "reason": "missing_access_token"}

        if not self.endpoint:
            return {"ok": False, "reason": "missing_endpoint"}

        headers = {
            "access_token": self.access_token,
            "Content-Type": "application/json",
        }

        payload = {
            "recipient": {"user_id": user_id},
            "message": {"text": text},
        }

        try:
            resp = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            return {
                "ok": resp.ok,
                "status_code": resp.status_code,
                "body": resp.text,
            }
        except Exception as ex:
            return {
                "ok": False,
                "reason": "request_exception",
                "error": str(ex),
            }

    def send_text_to_many(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for user_id in self.recipients:
            r = self.send_text(user_id=user_id, text=text)
            r["user_id"] = user_id
            results.append(r)
        return results