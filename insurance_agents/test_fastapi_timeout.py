#!/usr/bin/env python3
"""
FastAPI Timeout Configuration Checker
This script will check the FastAPI server timeout configurations
"""

import asyncio
import httpx
import time
from datetime import datetime

async def test_fastapi_timeout():
    """Test FastAPI timeout behavior specifically"""
    
    print("🔧 Testing FastAPI Timeout Configuration")
    print(f"🕒 Start time: {datetime.now().strftime('%H:%M:%S')}")
    
    orchestrator_url = "http://localhost:8001"
    
    # Test with a request that should take long time
    long_request = {
        "message": "process the claim for claim id OP-05",
        "sessionId": f"fastapi_timeout_test_{int(time.time())}",
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📤 Sending long-running request to test timeout...")
    
    # Test with different timeout configurations
    test_timeouts = [
        ("30s", 30.0),
        ("60s", 60.0), 
        ("90s", 90.0),
        ("5min", 300.0),
        ("10min", 600.0)
    ]
    
    for timeout_name, timeout_seconds in test_timeouts:
        print(f"\n🔍 Testing with {timeout_name} timeout ({timeout_seconds}s)")
        
        try:
            start_time = time.time()
            
            timeout_config = httpx.Timeout(
                connect=10.0,
                read=timeout_seconds,
                write=10.0,
                pool=10.0
            )
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{orchestrator_url}/api/chat",
                    json=long_request,
                    headers={"Content-Type": "application/json"}
                )
                
                elapsed = time.time() - start_time
                print(f"✅ {timeout_name} test COMPLETED in {elapsed:.1f}s")
                print(f"📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    preview = str(response_data.get('response', ''))[:100]
                    print(f"📄 Response: {preview}...")
                    return True  # Success on first working timeout
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            print(f"⏰ {timeout_name} test TIMED OUT after {elapsed:.1f}s")
            print(f"   Timeout type: {type(e).__name__}")
            print(f"   Details: {str(e)}")
            
        except httpx.ConnectError as e:
            print(f"🔌 {timeout_name} test CONNECTION ERROR: {e}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {timeout_name} test ERROR after {elapsed:.1f}s: {e}")
    
    return False

async def test_keep_alive_behavior():
    """Test if the connection is being kept alive properly"""
    
    print("\n🔄 Testing Keep-Alive Behavior")
    
    orchestrator_url = "http://localhost:8001"
    
    # Send multiple requests with the same client to test keep-alive
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        
        for i in range(3):
            print(f"\n📤 Request {i+1}/3")
            
            request_data = {
                "message": f"test request {i+1}",
                "sessionId": f"keepalive_test_{int(time.time())}_{i}",
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                start_time = time.time()
                response = await client.post(f"{orchestrator_url}/api/chat", json=request_data)
                elapsed = time.time() - start_time
                
                print(f"✅ Request {i+1} completed in {elapsed:.1f}s")
                print(f"📊 Status: {response.status_code}")
                print(f"🔗 Connection header: {response.headers.get('connection', 'not set')}")
                
                if i < 2:  # Wait between requests except the last one
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"❌ Request {i+1} failed: {e}")

async def check_uvicorn_default_timeout():
    """Check what uvicorn default timeout might be"""
    
    print("\n🔍 Checking Uvicorn Default Timeout Behavior")
    
    # Make a request that should trigger orchestrator processing
    print("📤 Making a request to trigger full orchestrator workflow...")
    
    start_time = time.time()
    
    try:
        # Use a very long timeout to see if uvicorn cuts us off
        async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as client:  # 15 minutes
            
            response = await client.post(
                "http://localhost:8001/api/chat",
                json={
                    "message": "process the claim for claim id OP-05",
                    "sessionId": f"uvicorn_test_{int(time.time())}",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Uvicorn test completed in {elapsed:.1f}s")
            print(f"📊 Status: {response.status_code}")
            
            return True, elapsed
            
    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        print(f"⏰ Uvicorn test timed out after {elapsed:.1f}s")
        print(f"   This suggests the timeout is around {elapsed:.0f} seconds")
        return False, elapsed
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Uvicorn test error after {elapsed:.1f}s: {e}")
        return False, elapsed

async def main():
    """Run all FastAPI timeout tests"""
    
    print("🚀 FastAPI Timeout Configuration Checker")
    print("=" * 60)
    
    # Test 1: Different timeout configurations
    print("🔍 TEST 1: Different Client Timeout Configurations")
    success1 = await test_fastapi_timeout()
    
    print("\n" + "=" * 60)
    
    # Test 2: Keep-alive behavior
    print("🔍 TEST 2: Keep-Alive Connection Behavior") 
    await test_keep_alive_behavior()
    
    print("\n" + "=" * 60)
    
    # Test 3: Uvicorn default timeout
    print("🔍 TEST 3: Uvicorn Default Timeout Detection")
    success3, uvicorn_timeout = await check_uvicorn_default_timeout()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   FastAPI request test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Uvicorn timeout test: {'✅ PASS' if success3 else f'❌ TIMEOUT at {uvicorn_timeout:.0f}s'}")
    
    if not success3 and uvicorn_timeout < 120:  # Less than 2 minutes
        print("\n🚨 LIKELY ISSUE FOUND:")
        print(f"   Uvicorn appears to timeout at ~{uvicorn_timeout:.0f} seconds")
        print("   This matches the UI timeout issue timing!")
        print("\n💡 SOLUTION:")
        print("   Need to configure uvicorn with longer timeout:")
        print("   uvicorn.run(app, timeout_keep_alive=600)  # 10 minutes")

if __name__ == "__main__":
    asyncio.run(main())
