"""
Sample Student Submission: Fibonacci Calculator

This is an example submission for testing the grading system.
It has some good aspects and some areas for improvement.
"""


def fibonacci(n):
    """Calculate the nth Fibonacci number using recursion.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_list(count):
    """Generate a list of Fibonacci numbers.
    
    Args:
        count: How many Fibonacci numbers to generate
        
    Returns:
        List of Fibonacci numbers
    """
    result = []
    for i in range(count):
        result.append(fibonacci(i))
    return result


# Main execution
if __name__ == "__main__":
    # Print first 10 Fibonacci numbers
    print("First 10 Fibonacci numbers:")
    numbers = fibonacci_list(10)
    for i, num in enumerate(numbers):
        print(f"F({i}) = {num}")
