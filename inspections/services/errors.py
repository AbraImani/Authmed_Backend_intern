"""Controlled analysis outcomes; none represents a medicine authenticity claim."""


class ProcessingError(RuntimeError):
    code = "processing_failed"


class InsufficientData(ProcessingError):
    code = "insufficient_data"


class ProviderUnavailable(ProcessingError):
    code = "provider_unavailable"


class IncompleteAnalysis(ProcessingError):
    code = "incomplete_analysis"


class ProcessingCancelled(ProcessingError):
    code = "cancelled"
