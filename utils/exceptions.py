"""Utilities for exceptions."""


def leaves[ExcT](exception_group: ExceptionGroup[ExcT]) -> list[ExcT]:
    """
    Flattens exception groups into a list of exceptions.

    :param exception_group: Exception group
    :return: List of exceptions in a group
    """
    def to_list_ref(eg: ExceptionGroup[ExcT], lst: list[ExcT]) -> list[ExcT]:
        for exc in eg.exceptions:
            if isinstance(exc, ExceptionGroup):
                to_list_ref(exc, lst)
            else:
                lst.append(exc)
        return lst

    return to_list_ref(exception_group, [])
