import math

def factorial(n: int) -> int:
    """
    Calculate the factorial of a number using recursion.

    Args:
        n (int): The input number to calculate the factorial for.

    Returns:
        int: The calculated factorial value.

    Raises:
        ValueError: If the input number is negative.
    """
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)