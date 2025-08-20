#!/usr/bin/env python3
"""
Advanced MCP Server Example using QuickMCP

This example demonstrates more advanced features including:
- Async tools and resources
- SSE transport for network access
- Context injection
- Error handling
- Database integration (simulated)

To run as stdio:
    python advanced_server.py

To run as SSE server:
    python advanced_server.py --transport sse --port 8080

Then connect with:
    mcp-client sse http://localhost:8080/sse
"""

import argparse
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import random
from quickmcp import QuickMCPServer, Context

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Advanced QuickMCP Server")
parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--host", default="localhost")
args = parser.parse_args()

# Create the server
server = QuickMCPServer(
    name="advanced-quickmcp",
    version="2.0.0",
    description="Advanced MCP server with async operations and database simulation"
)

# Simulated database
class Database:
    """Simulated async database."""
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    async def create_user(self, name: str, email: str) -> Dict[str, Any]:
        """Create a new user."""
        await asyncio.sleep(0.1)  # Simulate DB delay
        user_id = f"user_{self.next_id}"
        self.next_id += 1
        
        user = {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "tasks": []
        }
        self.users[user_id] = user
        return user
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        await asyncio.sleep(0.05)  # Simulate DB delay
        return self.users.get(user_id)
    
    async def create_task(self, user_id: str, title: str, description: str) -> Dict[str, Any]:
        """Create a new task for a user."""
        await asyncio.sleep(0.1)  # Simulate DB delay
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        task_id = f"task_{self.next_id}"
        self.next_id += 1
        
        task = {
            "id": task_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.tasks[task_id] = task
        self.users[user_id]["tasks"].append(task_id)
        
        return task
    
    async def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark a task as completed."""
        await asyncio.sleep(0.05)  # Simulate DB delay
        
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        
        return task
    
    async def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a user."""
        await asyncio.sleep(0.05)  # Simulate DB delay
        
        if user_id not in self.users:
            return []
        
        task_ids = self.users[user_id]["tasks"]
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]

# Initialize database
db = Database()


# ====================
# Async Tools
# ====================

@server.tool(description="Create a new user in the system")
async def create_user(name: str, email: str) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        name: User's full name
        email: User's email address
    
    Returns:
        The created user object
    """
    try:
        user = await db.create_user(name, email)
        return {
            "success": True,
            "user": user,
            "message": f"User {name} created successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@server.tool()
async def get_user(user_id: str) -> Dict[str, Any]:
    """Get user information by ID."""
    user = await db.get_user(user_id)
    
    if user:
        return {
            "success": True,
            "user": user
        }
    else:
        return {
            "success": False,
            "error": f"User {user_id} not found"
        }


@server.tool()
async def create_task(user_id: str, title: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new task for a user.
    
    Args:
        user_id: ID of the user
        title: Task title
        description: Optional task description
    
    Returns:
        The created task
    """
    try:
        task = await db.create_task(user_id, title, description)
        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created for user {user_id}"
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }


@server.tool()
async def complete_task(task_id: str) -> Dict[str, Any]:
    """Mark a task as completed."""
    try:
        task = await db.complete_task(task_id)
        return {
            "success": True,
            "task": task,
            "message": f"Task {task_id} marked as completed"
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }


@server.tool()
async def get_user_tasks(user_id: str, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all tasks for a user.
    
    Args:
        user_id: ID of the user
        status: Optional filter by status (pending/completed)
    
    Returns:
        List of user's tasks
    """
    tasks = await db.get_user_tasks(user_id)
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    return {
        "success": True,
        "user_id": user_id,
        "tasks": tasks,
        "count": len(tasks)
    }


@server.tool()
async def analyze_productivity(user_id: str) -> Dict[str, Any]:
    """Analyze user productivity metrics."""
    user = await db.get_user(user_id)
    
    if not user:
        return {
            "success": False,
            "error": f"User {user_id} not found"
        }
    
    tasks = await db.get_user_tasks(user_id)
    
    completed = [t for t in tasks if t["status"] == "completed"]
    pending = [t for t in tasks if t["status"] == "pending"]
    
    # Calculate metrics
    completion_rate = len(completed) / len(tasks) * 100 if tasks else 0
    
    # Simulate some advanced metrics
    avg_completion_time = random.uniform(1, 5)  # hours
    productivity_score = min(100, completion_rate + random.uniform(-10, 10))
    
    return {
        "success": True,
        "user_id": user_id,
        "metrics": {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "completion_rate": round(completion_rate, 2),
            "avg_completion_time_hours": round(avg_completion_time, 2),
            "productivity_score": round(productivity_score, 2)
        },
        "recommendations": [
            "Consider breaking down large tasks into smaller ones" if len(pending) > 5 else None,
            "Great job maintaining high completion rate!" if completion_rate > 80 else None,
            "Try to complete pending tasks to improve productivity" if len(pending) > len(completed) else None
        ]
    }


# ====================
# Resources
# ====================

@server.resource("user://{user_id}")
async def get_user_resource(user_id: str) -> str:
    """Get user data as a resource."""
    user = await db.get_user(user_id)
    
    if user:
        tasks = await db.get_user_tasks(user_id)
        user_data = {
            **user,
            "tasks_detail": tasks
        }
        return json.dumps(user_data, indent=2)
    else:
        return json.dumps({"error": f"User {user_id} not found"})


@server.resource("stats://overview")
async def get_system_stats() -> str:
    """Get system statistics."""
    total_users = len(db.users)
    total_tasks = len(db.tasks)
    completed_tasks = len([t for t in db.tasks.values() if t["status"] == "completed"])
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "users": {
            "total": total_users,
            "active": total_users  # Simplified
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": total_tasks - completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        },
        "server": {
            "name": server.name,
            "version": server.version,
            "uptime": "N/A"  # Would track in real implementation
        }
    }
    
    return json.dumps(stats, indent=2)


# ====================
# Prompts
# ====================

@server.prompt()
def task_planning(user_name: str, goals: str) -> str:
    """Generate a task planning prompt."""
    return f"""Help {user_name} create a task plan to achieve the following goals:

{goals}

Please:
1. Break down the goals into specific, actionable tasks
2. Suggest a priority order for the tasks
3. Estimate time requirements for each task
4. Identify potential dependencies between tasks
5. Recommend milestones to track progress

Format the response as a structured task list that can be easily imported into a task management system."""


@server.prompt()
def productivity_coaching(metrics: Dict[str, Any]) -> str:
    """Generate productivity coaching based on metrics."""
    return f"""Based on the following productivity metrics:

{json.dumps(metrics, indent=2)}

Provide personalized productivity coaching that includes:
1. Analysis of current performance
2. Identification of strengths and areas for improvement
3. Specific, actionable recommendations
4. Suggested daily/weekly routines
5. Tools or techniques that might help
6. Motivational insights

Keep the tone supportive and encouraging."""


# ====================
# Main entry point
# ====================

if __name__ == "__main__":
    print(f"Starting {server.name} v{server.version}")
    print(f"Transport: {args.transport}")
    
    if args.transport == "sse":
        print(f"URL: http://{args.host}:{args.port}/sse")
    
    print(f"\nAvailable tools: {', '.join(server.list_tools())}")
    print(f"Available resources: {', '.join(server.list_resources())}")
    print(f"Available prompts: {', '.join(server.list_prompts())}")
    print("-" * 50)
    
    # Run the server with specified transport
    server.run(
        transport=args.transport,
        host=args.host,
        port=args.port
    )