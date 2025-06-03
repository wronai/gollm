import math

def factorial(n):
    """
    Calculate the factorial of a given number using recursion.

    Args:
        n (int): The input number to calculate the factorial for.

    Returns:
        int: The calculated factorial.

    Raises:
        ValueError: If the input number is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)