from models.lead import LeadRecord
from utils.logger import get_logger

logger = get_logger(__name__)


class NotificationTool:
    def __init__(self, webhook_url: str = None, email_client=None):
        self._webhook_url = webhook_url
        self._email_client = email_client

    def notify_lead(self, record: LeadRecord) -> bool:
        try:
            self._send_slack(record)
            logger.info("lead_notification_sent", email=record.lead_data.email)
            return True
        except Exception as exc:
            logger.error("lead_notification_failed", error=str(exc))
            return False

    def notify_error(self, session_id: str, error_code: str, detail: str) -> None:
        logger.error(
            "system_error_notification",
            session_id=session_id,
            error_code=error_code,
            detail=detail,
        )

    def _send_slack(self, record: LeadRecord) -> None:
        pass

    def _send_email(self, record: LeadRecord) -> None:
        pass
