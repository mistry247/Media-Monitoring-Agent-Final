#!/usr/bin/env python3
"""
Quick test script for health check functionality
"""
import asyncio
from utils.health_check import get_health_status

async def main():
    print("Testing health check system...")
    try:
        result = await get_health_status()
        print(f"Health status: {result['status']}")
        print(f"Total checks: {result['summary']['total_checks']}")
        print(f"Healthy: {result['summary']['healthy']}")
        print(f"Degraded: {result['summary']['degraded']}")
        print(f"Unhealthy: {result['summary']['unhealthy']}")
        
        print("\nIndividual check results:")
        for check_name, check_result in result['checks'].items():
            print(f"  {check_name}: {check_result['status']} - {check_result['message']}")
            
    except Exception as e:
        print(f"Error running health checks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())