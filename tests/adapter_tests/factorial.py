import math

def factorial(n):
    """Calculate the factorial of a number using recursion.

    Args:
        n (int): The input number.

    Returns:
        int: The factorial of the input number.

    Raises:
        ValueError: If the input number is negative.
    """
    if n < 0:
        raise ValueError("Input number must be non-negative.")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)