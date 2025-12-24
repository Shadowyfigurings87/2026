# services/alert_engine.py

import threading
import requests
import smtplib
from email.mime.text import MIMEText

from utils.logging_config import log_event


class AlertEngine:
    def __init__(self):
        # Optional alert channels
        self.discord_webhook = None
        self.email_config = None
        self.webhook_url = None

        log_event("alert_engine", "INFO", "engine_initialized", {})

    # -----------------------------
    # Configuration
    # -----------------------------
    def configure_discord(self, webhook_url: str):
        self.discord_webhook = webhook_url
        log_event("alert_engine", "INFO", "discord_configured", {})

    def configure_email(self, smtp_host, smtp_port, username, password, to_addr):
        self.email_config = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "to_addr": to_addr,
        }
        log_event("alert_engine", "INFO", "email_configured", {})

    def configure_webhook(self, url: str):
        self.webhook_url = url
        log_event("alert_engine", "INFO", "webhook_configured", {})

    # -----------------------------
    # Public API
    # -----------------------------
    def send_alert(self, frame: dict):
        """
        Dispatch an alert asynchronously.
        """
        t = threading.Thread(target=self._dispatch, args=(frame,), daemon=True)
        t.start()

    # -----------------------------
    # Internal: dispatch logic
    # -----------------------------
    def _dispatch(self, frame: dict):
        """
        Send alerts to all configured channels.
        """
        msg = self._format_message(frame)

        # Always log locally
        log_event("alert_engine", "ALERT", "anomaly_alert", msg)

        # Discord
        if self.discord_webhook:
            try:
                requests.post(self.discord_webhook, json={"content": msg})
            except Exception as e:
                log_event("alert_engine", "ERROR", "discord_failed", {"error": str(e)})

        # Email
        if self.email_config:
            try:
                self._send_email(msg)
            except Exception as e:
                log_event("alert_engine", "ERROR", "email_failed", {"error": str(e)})

        # Generic webhook
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=msg)
            except Exception as e:
                log_event("alert_engine", "ERROR", "webhook_failed", {"error": str(e)})

    # -----------------------------
    # Internal: email sending
    # -----------------------------
    def _send_email(self, msg: str):
        cfg = self.email_config
        mime = MIMEText(msg)
        mime["Subject"] = "RF Observatory Alert"
        mime["From"] = cfg["username"]
        mime["To"] = cfg["to_addr"]

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["username"], cfg["password"])
            server.sendmail(cfg["username"], cfg["to_addr"], mime.as_string())

    # -----------------------------
    # Internal: message formatting
    # -----------------------------
    def _format_message(self, frame: dict) -> str:
        """
        Create a human-readable alert message.
        """
        return (
            f"⚠️ RF Anomaly Detected\n"
            f"Severity: {frame.get('anomaly_severity')}\n"
            f"Score: {frame.get('anomaly_score')}\n"
            f"Cluster: {frame.get('anomaly_cluster')}\n"
            f"Device deviation: {frame.get('device_deviation')}\n"
            f"Channel deviation: {frame.get('channel_deviation')}\n"
            f"Frame type: {frame.get('frame_type')}\n"
            f"Source: {frame.get('src')}\n"
            f"Channel: {frame.get('channel')}\n"
            f"Timestamp: {frame.get('timestamp')}"
        )


# Singleton instance
engine = AlertEngine()
