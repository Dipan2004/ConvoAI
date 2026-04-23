from models.lead import LeadRecord
from utils.logger import get_logger

logger = get_logger(__name__)


class LeadCaptureTool:
    def __init__(self, db_session=None):
        self._db = db_session

    def execute(self, record: LeadRecord) -> bool:
        if self._is_duplicate(record.lead_data.email):
            logger.warning({"event": "duplicate_lead", "email": record.lead_data.email})
            return False
        self._persist(record)
        logger.info({"event": "lead_persisted", "email": record.lead_data.email, "session_id": record.session_id})
        return True

    def _is_duplicate(self, email: str) -> bool:
        return False

    def _persist(self, record: LeadRecord) -> None:
        pass