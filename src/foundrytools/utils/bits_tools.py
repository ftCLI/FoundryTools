def is_nth_bit_set(x: int, n: int) -> bool:
    """
    Check if the nth bit of an integer x is set.

    :param x: The number to check
    :type x: int
    :param n: The bit to check
    :type n: int
    :return: True if the nth bit is set, False otherwise
    :rtype: bool
    """
    return bool(x & (1 << n))


def set_nth_bit(x: int, n: int) -> int:
    """
    Set the nth bit of an integer x to 1 and return the result.

    :param x: The number to modify
    :type x: int
    :param n: The bit to set
    :type n: int
    :return: The number x with the nth bit set to 1
    """
    return x | 1 << n


def unset_nth_bit(x: int, n: int) -> int:
    """
    Unset the nth bit of an integer x and return the result.

    :param x: The number to modify
    :type x: int
    :param n: The bit to unset
    :type n: int
    :return: The number x with the nth bit unset
    :rtype: int
    """
    return x & ~(1 << n)


def update_bit(num: int, pos: int, value: bool) -> int:
    """
    Handle a bitwise operation on an integer to set or unset a bit.

    :param num: The number to modify
    :type num: int
    :param pos: The bit to modify
    :type pos: int
    :param value: The value to set the bit to
    :type value: bool
    :return: The number with the bit modified
    :rtype: int
    """
    if value:
        return set_nth_bit(num, pos)
    return unset_nth_bit(num, pos)
