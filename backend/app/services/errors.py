class ServiceError(Exception):
    pass


class BadRequestError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class ForbiddenError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class ExternalServiceError(ServiceError):
    pass
