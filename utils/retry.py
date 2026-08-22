import logging


def after_func(retry_state):
    """Log warning after a failed attempt."""
    exc = retry_state.outcome.exception()
    logging.warning(
        f"Retry attempt {retry_state.attempt_number} failed: {exc}. "
        f"Waiting before retry..."
    )
