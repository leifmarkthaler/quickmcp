#!/usr/bin/env python
"""
Math Server - A simple mathematical operations MCP server.

This example demonstrates basic QuickMCP features with a collection
of mathematical tools, resources, and prompts.
"""

import math
import random
import statistics
from typing import List, Union, Optional
from quickmcp import QuickMCPServer

# Create the server
server = QuickMCPServer(
    name="math-server",
    version="1.0.0",
    description="Mathematical operations and calculations server"
)

# ============= Basic Arithmetic Tools =============

@server.tool()
def calculate(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Result of the calculation
    """
    # Safe evaluation - only allow math operations
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    allowed_names.update({
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
    })
    
    try:
        # Remove any potentially dangerous characters
        expression = expression.replace("import", "").replace("__", "")
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


@server.tool()
def basic_operations(a: float, b: float) -> dict:
    """
    Perform all basic operations on two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Dictionary with all basic operation results
    """
    return {
        "addition": a + b,
        "subtraction": a - b,
        "multiplication": a * b,
        "division": a / b if b != 0 else "undefined",
        "power": a ** b,
        "modulo": a % b if b != 0 else "undefined",
        "floor_division": a // b if b != 0 else "undefined"
    }


# ============= Statistics Tools =============

@server.tool()
def statistics_summary(numbers: List[float]) -> dict:
    """
    Calculate statistical summary of a list of numbers.
    
    Args:
        numbers: List of numbers to analyze
        
    Returns:
        Statistical summary including mean, median, mode, etc.
    """
    if not numbers:
        return {"error": "Empty list provided"}
    
    sorted_nums = sorted(numbers)
    
    summary = {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": statistics.mean(numbers),
        "median": statistics.median(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "range": max(numbers) - min(numbers)
    }
    
    # Add mode if it exists
    try:
        summary["mode"] = statistics.mode(numbers)
    except statistics.StatisticsError:
        summary["mode"] = "No unique mode"
    
    # Add standard deviation and variance for lists with more than 1 element
    if len(numbers) > 1:
        summary["std_dev"] = statistics.stdev(numbers)
        summary["variance"] = statistics.variance(numbers)
        summary["quartiles"] = {
            "Q1": statistics.quantiles(numbers, n=4)[0],
            "Q2": statistics.quantiles(numbers, n=4)[1],
            "Q3": statistics.quantiles(numbers, n=4)[2]
        }
    
    return summary


@server.tool()
def linear_regression(x_values: List[float], y_values: List[float]) -> dict:
    """
    Perform simple linear regression on two sets of values.
    
    Args:
        x_values: X coordinates
        y_values: Y coordinates
        
    Returns:
        Slope, intercept, and correlation coefficient
    """
    if len(x_values) != len(y_values):
        return {"error": "X and Y lists must have the same length"}
    
    if len(x_values) < 2:
        return {"error": "Need at least 2 points for regression"}
    
    n = len(x_values)
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)
    
    # Calculate slope
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    
    if denominator == 0:
        return {"error": "Cannot perform regression - all X values are the same"}
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate correlation coefficient
    if len(x_values) > 2:
        try:
            correlation = statistics.correlation(x_values, y_values)
        except:
            correlation = None
    else:
        correlation = 1.0 if slope > 0 else -1.0
    
    return {
        "slope": slope,
        "intercept": intercept,
        "correlation": correlation,
        "equation": f"y = {slope:.4f}x + {intercept:.4f}"
    }


# ============= Geometry Tools =============

@server.tool()
def geometry_circle(radius: float) -> dict:
    """
    Calculate circle properties.
    
    Args:
        radius: Circle radius
        
    Returns:
        Area, circumference, and diameter
    """
    if radius < 0:
        return {"error": "Radius must be non-negative"}
    
    return {
        "radius": radius,
        "diameter": 2 * radius,
        "circumference": 2 * math.pi * radius,
        "area": math.pi * radius ** 2
    }


@server.tool()
def geometry_triangle(a: float, b: float, c: float) -> dict:
    """
    Calculate triangle properties from three sides.
    
    Args:
        a: First side length
        b: Second side length
        c: Third side length
        
    Returns:
        Triangle properties including area, perimeter, and angles
    """
    # Check triangle inequality
    if a + b <= c or a + c <= b or b + c <= a:
        return {"error": "Invalid triangle - sides don't satisfy triangle inequality"}
    
    if a <= 0 or b <= 0 or c <= 0:
        return {"error": "All sides must be positive"}
    
    # Calculate semi-perimeter
    s = (a + b + c) / 2
    
    # Heron's formula for area
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    
    # Calculate angles using law of cosines
    angle_A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
    angle_B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
    angle_C = 180 - angle_A - angle_B
    
    # Determine triangle type
    angles = sorted([angle_A, angle_B, angle_C])
    if abs(angles[2] - 90) < 0.001:
        triangle_type = "right"
    elif angles[2] > 90:
        triangle_type = "obtuse"
    else:
        triangle_type = "acute"
    
    # Check if equilateral, isosceles, or scalene
    sides = sorted([a, b, c])
    if abs(sides[0] - sides[2]) < 0.001:
        side_type = "equilateral"
    elif abs(sides[0] - sides[1]) < 0.001 or abs(sides[1] - sides[2]) < 0.001:
        side_type = "isosceles"
    else:
        side_type = "scalene"
    
    return {
        "sides": {"a": a, "b": b, "c": c},
        "perimeter": a + b + c,
        "area": area,
        "angles": {
            "A": angle_A,
            "B": angle_B,
            "C": angle_C
        },
        "triangle_type": triangle_type,
        "side_type": side_type,
        "inradius": area / s,
        "circumradius": (a * b * c) / (4 * area)
    }


# ============= Number Theory Tools =============

@server.tool()
def prime_check(n: int) -> dict:
    """
    Check if a number is prime and find factors.
    
    Args:
        n: Number to check
        
    Returns:
        Prime status and factors
    """
    if n < 2:
        return {"is_prime": False, "reason": "Less than 2"}
    
    factors = []
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            factors.append(i)
            if i != n // i:
                factors.append(n // i)
    
    if factors:
        factors.sort()
        return {
            "number": n,
            "is_prime": False,
            "factors": [1] + factors + [n],
            "prime_factors": prime_factorization(n)
        }
    else:
        return {
            "number": n,
            "is_prime": True,
            "factors": [1, n]
        }


def prime_factorization(n: int) -> List[int]:
    """Get prime factorization of a number."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


@server.tool()
def fibonacci(n: int) -> dict:
    """
    Generate Fibonacci sequence.
    
    Args:
        n: Number of terms to generate
        
    Returns:
        Fibonacci sequence and properties
    """
    if n <= 0:
        return {"error": "Number must be positive"}
    
    if n > 100:
        return {"error": "Maximum 100 terms allowed"}
    
    sequence = []
    a, b = 0, 1
    
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    
    return {
        "count": n,
        "sequence": sequence,
        "sum": sum(sequence),
        "last_term": sequence[-1],
        "golden_ratio_approximation": sequence[-1] / sequence[-2] if n > 1 else None
    }


# ============= Random Number Tools =============

@server.tool()
def random_numbers(
    count: int = 10,
    min_value: float = 0,
    max_value: float = 100,
    integers_only: bool = False,
    seed: Optional[int] = None
) -> dict:
    """
    Generate random numbers.
    
    Args:
        count: Number of random numbers to generate
        min_value: Minimum value
        max_value: Maximum value
        integers_only: Generate only integers
        seed: Random seed for reproducibility
        
    Returns:
        Generated random numbers and statistics
    """
    if count <= 0 or count > 1000:
        return {"error": "Count must be between 1 and 1000"}
    
    if min_value >= max_value:
        return {"error": "Min value must be less than max value"}
    
    if seed is not None:
        random.seed(seed)
    
    if integers_only:
        numbers = [random.randint(int(min_value), int(max_value)) for _ in range(count)]
    else:
        numbers = [random.uniform(min_value, max_value) for _ in range(count)]
    
    return {
        "count": count,
        "range": [min_value, max_value],
        "numbers": numbers,
        "statistics": statistics_summary(numbers)
    }


# ============= Resources =============

@server.resource("constants://{name}")
def math_constants(name: str) -> str:
    """
    Get mathematical constants.
    
    Args:
        name: Constant name (pi, e, tau, phi, etc.)
        
    Returns:
        Value and description of the constant
    """
    constants = {
        "pi": (math.pi, "Ratio of circle's circumference to diameter"),
        "e": (math.e, "Euler's number, base of natural logarithm"),
        "tau": (math.tau, "2π, full circle in radians"),
        "phi": ((1 + math.sqrt(5)) / 2, "Golden ratio"),
        "sqrt2": (math.sqrt(2), "Square root of 2, Pythagorean constant"),
        "sqrt3": (math.sqrt(3), "Square root of 3"),
        "ln2": (math.log(2), "Natural logarithm of 2"),
        "ln10": (math.log(10), "Natural logarithm of 10"),
    }
    
    if name.lower() in constants:
        value, description = constants[name.lower()]
        return f"{name}: {value}\n{description}"
    else:
        available = ", ".join(constants.keys())
        return f"Unknown constant: {name}\nAvailable: {available}"


@server.resource("formulas://{topic}")
def math_formulas(topic: str) -> str:
    """
    Get mathematical formulas for a topic.
    
    Args:
        topic: Topic name (geometry, algebra, calculus, etc.)
        
    Returns:
        Common formulas for the topic
    """
    formulas = {
        "geometry": """Geometry Formulas:
- Circle Area: πr²
- Circle Circumference: 2πr
- Triangle Area: ½bh or √(s(s-a)(s-b)(s-c))
- Rectangle Area: length × width
- Sphere Volume: (4/3)πr³
- Sphere Surface Area: 4πr²
- Cylinder Volume: πr²h
- Cone Volume: (1/3)πr²h""",
        
        "algebra": """Algebra Formulas:
- Quadratic Formula: x = (-b ± √(b²-4ac))/(2a)
- Distance Formula: d = √((x₂-x₁)² + (y₂-y₁)²)
- Slope: m = (y₂-y₁)/(x₂-x₁)
- Point-Slope Form: y - y₁ = m(x - x₁)
- Binomial Theorem: (a+b)ⁿ = Σ(n choose k)aⁿ⁻ᵏbᵏ""",
        
        "trigonometry": """Trigonometry Formulas:
- Pythagorean Identity: sin²θ + cos²θ = 1
- Double Angle: sin(2θ) = 2sin(θ)cos(θ)
- Law of Sines: a/sin(A) = b/sin(B) = c/sin(C)
- Law of Cosines: c² = a² + b² - 2ab·cos(C)""",
        
        "calculus": """Calculus Formulas:
- Power Rule: d/dx(xⁿ) = nxⁿ⁻¹
- Product Rule: d/dx(fg) = f'g + fg'
- Chain Rule: d/dx(f(g(x))) = f'(g(x))·g'(x)
- Integration by Parts: ∫udv = uv - ∫vdu"""
    }
    
    if topic.lower() in formulas:
        return formulas[topic.lower()]
    else:
        available = ", ".join(formulas.keys())
        return f"Unknown topic: {topic}\nAvailable topics: {available}"


# ============= Prompts =============

@server.prompt()
def solve_problem(problem_type: str, details: str) -> str:
    """
    Generate a problem-solving prompt.
    
    Args:
        problem_type: Type of math problem
        details: Problem details
        
    Returns:
        Structured problem-solving prompt
    """
    return f"""Please solve this {problem_type} problem:

{details}

Please provide:
1. Problem analysis and understanding
2. Step-by-step solution
3. Final answer
4. Verification of the result
5. Alternative approaches (if applicable)

Show all work and explain each step clearly."""


@server.prompt()
def explain_concept(concept: str, level: str = "intermediate") -> str:
    """
    Generate a concept explanation prompt.
    
    Args:
        concept: Mathematical concept to explain
        level: Difficulty level (beginner, intermediate, advanced)
        
    Returns:
        Explanation prompt
    """
    return f"""Please explain the mathematical concept of {concept} at a {level} level.

Include:
1. Clear definition
2. Key properties and characteristics
3. Real-world applications
4. Common examples
5. Related concepts
6. Common misconceptions to avoid

Make the explanation accessible and include visual descriptions where helpful."""


# ============= Main =============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QuickMCP Math Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--port", type=int, default=8080)
    
    args = parser.parse_args()
    
    # Run server - QuickMCP handles logging to stderr automatically
    if args.transport == "sse":
        server.run(transport="sse", port=args.port)
    else:
        server.run(transport="stdio")