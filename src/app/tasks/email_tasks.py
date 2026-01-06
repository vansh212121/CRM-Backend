import logging
from app.core.celery_app import celery_app
from app.core import email

logger = logging.getLogger(__name__)


@celery_app.task
def send_acknowledgement_email_sync(email_to: str, name: str):
    """
    A Celery task that calls the synchronous email function to send acknowledgement email.
    """
    logger.info(f"Worker received task: send acknowledgement email to {email_to}")
    try:
        email.send_acknowledgement_email_sync(email_to=email_to, name=name)
        logger.info(f"Successfully sent acknowledgement email to {email_to}")
    except Exception as e:
        logger.error(
            f"Failed to send acknowledgement email to {email_to}: {e}", exc_info=True
        )


@celery_app.task
def send_confirmation_email_task(email_to: str, name: str, date_str: str):
    logger.info(f"Worker received task: send confirmation to {email_to}")
    try:
        email.send_confirmation_email_sync(
            email_to=email_to, name=name, date_str=date_str
        )
        logger.info(f"Successfully sent confirmation to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send confirmation to {email_to}: {e}", exc_info=True)


@celery_app.task
def send_followup_email_task(email_to: str, name: str):
    logger.info(f"Worker received task: send follow-up to {email_to}")
    try:
        email.send_followup_email_sync(email_to=email_to, name=name)
        logger.info(f"Successfully sent follow-up to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send follow-up to {email_to}: {e}", exc_info=True)


@celery_app.task
def send_booking_email_task(email_to: str, name: str, date_str: str):
    logger.info(f"Worker received task: send booking to {email_to}")
    try:
        email.send_booking_email_sync(email_to=email_to, name=name, date_str=date_str)
        logger.info(f"Successfully sent booking to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send booking to {email_to}: {e}", exc_info=True)


@celery_app.task
def send_reschedule_email_task(
    email_to: str, name: str, old_date_str: str, new_date_str: str
):
    logger.info(f"Worker received task: send reschedule notice to {email_to}")
    try:
        email.send_reschedule_email_sync(
            email_to=email_to,
            name=name,
            old_date_str=old_date_str,
            new_date_str=new_date_str,
        )
        logger.info(f"Successfully sent reschedule notice to {email_to}")
    except Exception as e:
        logger.error(
            f"Failed to send reschedule notice to {email_to}: {e}", exc_info=True
        )


@celery_app.task
def send_rejection_email_task(email_to: str, name: str, reason: str):
    logger.info(f"Worker received task: send rejection to {email_to}")
    try:
        email.send_rejection_email_sync(email_to=email_to, name=name, reason=reason)
        logger.info(f"Successfully sent rejection to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send rejection to {email_to}: {e}", exc_info=True)


@celery_app.task
def send_cancellation_email_task(email_to: str, name: str, reason: str):
    logger.info(f"Worker received task: send cancellation to {email_to}")
    try:
        email.send_cancellation_email_sync(email_to=email_to, name=name, reason=reason)
        logger.info(f"Successfully sent cancellation to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send cancellation to {email_to}: {e}", exc_info=True)
