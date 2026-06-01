class IngestionPersistenceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IngestionImmutabilityError(IngestionPersistenceError):
    pass


class IngestionPipelineStateError(IngestionPersistenceError):
    pass
