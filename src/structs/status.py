from enum import Enum


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


class WorkflowStatus(Enum):
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER_INPUT = "waiting_for_user_input"
    SUCCESS = "success"
    FAILURE = "failure"
