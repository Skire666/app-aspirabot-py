from enum import Enum


class StepExecutionResultEnum(Enum):
    """Enumerates the possible outcomes of a single step execution.

    Returned by every IStepExecutor.execute_logical() implementation.
    SUCCESS and WARNING are both treated as success for statistics purposes;
    ERROR and FATAL are both failures, but only FATAL stops the workflow.
    """

    E_UNSET = "UNSET"  # default value; should be overridden by executors
    E_SKIPPED = "SKIPPED"  # step was not executed due to a jump or section condition
    E_SUCCESS = "SUCCESS"  # step completed fully
    E_WARNING = "WARNING"  # completed with a non-critical anomaly; workflow continues
    E_ERROR = "ERROR"  # step failed; workflow continues to next step
    E_FATAL = "FATAL"  # step failed; workflow stops immediately
    E_UNKNOWN = "UNKNOWN"
