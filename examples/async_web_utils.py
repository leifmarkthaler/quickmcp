#!/usr/bin/env python
"""
Real-world async example: Web utilities as MCP tools.

This demonstrates how to create an MCP server with async web utilities
that can be used by AI assistants for web-related tasks.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import time
from urllib.parse import urlparse, urljoin
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp import create_mcp_from_module


# Mock async HTTP functions (in real use, would use aiohttp or httpx)
async def fetch_webpage(url: str, timeout: int = 10) -> Dict[str, any]:
    """
    Fetch a webpage and return its content and metadata.
    
    In production, this would use aiohttp or httpx.
    """
    await asyncio.sleep(0.5)  # Simulate network delay
    
    # Mock response based on URL
    parsed = urlparse(url)
    
    return {
        "url": url,
        "status": 200,
        "content": f"<html><body>Mock content for {parsed.netloc}</body></html>",
        "headers": {
            "content-type": "text/html",
            "content-length": "1234"
        },
        "fetch_time": 0.5,
        "timestamp": time.time()
    }


async def check_links(urls: List[str]) -> Dict[str, Dict]:
    """
    Check multiple URLs in parallel and return their status.
    
    Useful for validating links in documentation or websites.
    """
    async def check_single(url):
        await asyncio.sleep(0.2)  # Simulate check
        # Mock status check
        return {
            "url": url,
            "alive": not url.endswith("404"),
            "status": 404 if url.endswith("404") else 200,
            "response_time": 0.2
        }
    
    # Check all URLs in parallel
    results = await asyncio.gather(
        *[check_single(url) for url in urls],
        return_exceptions=True
    )
    
    return {
        "total": len(urls),
        "alive": sum(1 for r in results if isinstance(r, dict) and r.get("alive")),
        "dead": sum(1 for r in results if isinstance(r, dict) and not r.get("alive")),
        "results": [r if isinstance(r, dict) else {"url": urls[i], "error": str(r)} 
                   for i, r in enumerate(results)]
    }


async def extract_links(url: str, same_domain_only: bool = False) -> List[str]:
    """
    Extract all links from a webpage.
    
    Useful for crawling or analyzing site structure.
    """
    # Fetch the page
    page = await fetch_webpage(url)
    content = page.get("content", "")
    
    # Simple regex for href extraction (in production, use BeautifulSoup)
    href_pattern = r'href=[\'"]?([^\'" >]+)'
    links = re.findall(href_pattern, content)
    
    # Convert relative URLs to absolute
    parsed_base = urlparse(url)
    absolute_links = []
    
    for link in links:
        if link.startswith(('http://', 'https://')):
            absolute_links.append(link)
        else:
            absolute_links.append(urljoin(url, link))
    
    # Filter by domain if requested
    if same_domain_only:
        absolute_links = [
            link for link in absolute_links
            if urlparse(link).netloc == parsed_base.netloc
        ]
    
    return list(set(absolute_links))  # Remove duplicates


async def parallel_search(queries: List[str], search_engine: str = "mock") -> Dict[str, List]:
    """
    Search multiple queries in parallel.
    
    Useful for research tasks requiring multiple searches.
    """
    async def search_single(query):
        await asyncio.sleep(0.3)  # Simulate search
        # Mock search results
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result 1 for {query}",
                    "url": f"https://example.com/{query.replace(' ', '-')}/1",
                    "snippet": f"This is a result about {query}"
                },
                {
                    "title": f"Result 2 for {query}",
                    "url": f"https://example.com/{query.replace(' ', '-')}/2",
                    "snippet": f"Another result about {query}"
                }
            ],
            "search_time": 0.3
        }
    
    # Search all queries in parallel
    start = time.time()
    results = await asyncio.gather(*[search_single(q) for q in queries])
    total_time = time.time() - start
    
    return {
        "queries": queries,
        "engine": search_engine,
        "total_time": total_time,
        "average_time": total_time / len(queries) if queries else 0,
        "results": results
    }


async def monitor_websites(urls: List[str], interval: int = 60, duration: int = 300) -> Dict:
    """
    Monitor multiple websites over time.
    
    Useful for uptime monitoring or change detection.
    """
    if duration > 300:
        return {"error": "Maximum duration is 300 seconds"}
    
    if interval < 10:
        return {"error": "Minimum interval is 10 seconds"}
    
    # Calculate number of checks
    num_checks = min(duration // interval, 10)  # Max 10 checks
    
    results = {url: [] for url in urls}
    
    for check_num in range(num_checks):
        # Check all sites in parallel
        check_tasks = []
        for url in urls:
            async def check_site(site_url):
                await asyncio.sleep(0.1)  # Simulate check
                return {
                    "timestamp": time.time(),
                    "status": 200 if not site_url.endswith("down") else 503,
                    "response_time": 0.1
                }
            check_tasks.append(check_site(url))
        
        check_results = await asyncio.gather(*check_tasks)
        
        # Store results
        for url, result in zip(urls, check_results):
            results[url].append(result)
        
        # Wait for next interval (except on last check)
        if check_num < num_checks - 1:
            await asyncio.sleep(1)  # Use 1 second for demo instead of full interval
    
    # Calculate statistics
    stats = {}
    for url, checks in results.items():
        successful = sum(1 for c in checks if c["status"] == 200)
        stats[url] = {
            "uptime_percent": (successful / len(checks)) * 100 if checks else 0,
            "average_response_time": sum(c["response_time"] for c in checks) / len(checks) if checks else 0,
            "checks": checks
        }
    
    return {
        "urls": urls,
        "interval": interval,
        "duration": num_checks,  # Actual number of checks
        "statistics": stats
    }


async def batch_download(urls: List[str], max_concurrent: int = 5) -> Dict[str, Dict]:
    """
    Download multiple resources with concurrency control.
    
    Useful for bulk downloading with rate limiting.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_with_limit(url):
        async with semaphore:
            start = time.time()
            await asyncio.sleep(0.2)  # Simulate download
            
            # Mock download
            return {
                "url": url,
                "success": True,
                "size": len(url) * 100,  # Mock size
                "download_time": time.time() - start
            }
    
    # Download all with concurrency limit
    results = await asyncio.gather(
        *[download_with_limit(url) for url in urls],
        return_exceptions=True
    )
    
    # Process results
    successful = []
    failed = []
    
    for i, result in enumerate(results):
        if isinstance(result, dict):
            successful.append(result)
        else:
            failed.append({
                "url": urls[i],
                "error": str(result)
            })
    
    total_size = sum(r.get("size", 0) for r in successful)
    total_time = sum(r.get("download_time", 0) for r in successful)
    
    return {
        "total_urls": len(urls),
        "successful": len(successful),
        "failed": len(failed),
        "total_size": total_size,
        "average_time": total_time / len(successful) if successful else 0,
        "max_concurrent": max_concurrent,
        "results": {
            "successful": successful,
            "failed": failed
        }
    }


# Sync utilities that complement async ones
def parse_url(url: str) -> Dict[str, str]:
    """Parse a URL into its components."""
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "hostname": parsed.hostname,
        "port": parsed.port
    }


def build_url(base: str, path: str = "", params: Optional[Dict] = None) -> str:
    """Build a URL from components."""
    url = urljoin(base, path)
    
    if params:
        from urllib.parse import urlencode
        query = urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    
    return url


def extract_domain(url: str) -> str:
    """Extract the domain from a URL."""
    return urlparse(url).netloc


def main():
    """Demo the async web utilities."""
    print("Async Web Utilities MCP Server")
    print("=" * 60)
    
    async def demo():
        # Demo parallel link checking
        print("\n1. Checking multiple links in parallel...")
        urls = [
            "https://example.com",
            "https://example.com/404",  # Will be marked as dead
            "https://github.com"
        ]
        result = await check_links(urls)
        print(f"   Checked {result['total']} links: {result['alive']} alive, {result['dead']} dead")
        
        # Demo parallel search
        print("\n2. Searching multiple queries in parallel...")
        queries = ["python async", "mcp protocol", "web scraping"]
        results = await parallel_search(queries)
        print(f"   Searched {len(queries)} queries in {results['total_time']:.2f}s")
        print(f"   Average time per query: {results['average_time']:.2f}s")
        
        # Demo batch download
        print("\n3. Batch downloading with concurrency control...")
        download_urls = [f"https://example.com/file{i}.pdf" for i in range(10)]
        result = await batch_download(download_urls, max_concurrent=3)
        print(f"   Downloaded {result['successful']}/{result['total_urls']} files")
        print(f"   Max concurrent: {result['max_concurrent']}")
    
    # Run the demo
    asyncio.run(demo())
    
    print("\n" + "=" * 60)
    print("To run as MCP server:")
    print("  mcp-factory async_web_utils.py")
    print("\nAvailable async tools:")
    print("  - fetch_webpage: Fetch webpage content")
    print("  - check_links: Check multiple URLs in parallel")
    print("  - extract_links: Extract links from webpage")
    print("  - parallel_search: Search multiple queries")
    print("  - monitor_websites: Monitor site uptime")
    print("  - batch_download: Download with concurrency control")


if __name__ == "__main__":
    if "--run-server" in sys.argv:
        # Run as MCP server
        server = create_mcp_from_module(__file__, server_name="web-utils")
        server.run()
    else:
        main()