class SystemError(Exception):
    pass

class UserError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_error = True

    @property
    def user_error(self) ->bool:
        return self._user_error

class DatabaseQueryError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class DatabaseInsertError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class DocumentInsertError(DatabaseInsertError):
       def __init__(self, *args):
        super().__init__(*args)

class InvalidResourceIdentifier(UserError):
    def __init__(self, *args):
        super().__init__(*args)

class MissingGenerativeAction(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class GenerativeOutputError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class GenerativeExecutionError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class EmbeddingError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)

class FileReadError(UserError):
    def __init__(self, *args):
        super().__init__(*args)

class BulkUploadFailed(UserError):
    def __init__(self, *args):
        super().__init__(*args)

class InvalidGenerativeResponseStructure(UserError):
    def __init__(self, *args):
        super().__init__(*args)

class EmptyRFP(UserError):
    def __init__(self, *args):
        super().__init__(*args)

class StorageWriteError(SystemError):
    def __init__(self, *args):
        super().__init__(*args)
