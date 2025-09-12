#!/usr/bin/env python3
"""
Debug UI Timeout Issue
Comprehensive test to identify where the timeout is occurring between UI and Orchestrator
"""

import asyncio
import time
import httpx
import json
from datetime import datetime

class UITimeoutDebugger:
    def __init__(self):
        self.dashboard_url = "http://localhost:3000"  # Dashboard has /api/chat endpoint
        self.orchestrator_url = "http://localhost:8001"  # Orchestrator for direct A2A testing
        self.test_claim_id = "OP-05"
        self.start_time = None
        
    def log_with_timestamp(self, message):
        """Log message with precise timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🕒 [{timestamp}] {message}")
        
    async def test_ui_request_simulation(self):
        """Simulate the exact UI request with detailed logging"""
        self.log_with_timestamp("🚀 Starting UI request simulation")
        
        # Prepare the exact request that UI sends
        request_data = {
            "message": f"process the claim for claim id {self.test_claim_id}",
            "sessionId": f"debug_session_{int(time.time())}",
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_with_timestamp(f"📤 Sending request: {json.dumps(request_data, indent=2)}")
        
        # Use httpx for precise timeout control and logging
        timeout = httpx.Timeout(connect=10.0, read=600.0, write=10.0, pool=10.0)  # 10 minutes read timeout
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                self.start_time = time.time()
                self.log_with_timestamp("🔄 Making HTTP POST request to /api/chat")
                
                response = await client.post(
                    f"{self.dashboard_url}/api/chat",  # Use dashboard URL with /api/chat
                    json=request_data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Debug-UI-Timeout-Tester/1.0"
                    }
                )
                
                elapsed = time.time() - self.start_time
                self.log_with_timestamp(f"✅ Request completed successfully in {elapsed:.2f} seconds")
                self.log_with_timestamp(f"📊 Response status: {response.status_code}")
                self.log_with_timestamp(f"📋 Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log_with_timestamp(f"📄 Response preview: {str(response_data)[:200]}...")
                        return True, response_data
                    except Exception as e:
                        self.log_with_timestamp(f"❌ Failed to parse JSON response: {e}")
                        self.log_with_timestamp(f"📄 Raw response: {response.text[:500]}...")
                        return False, str(e)
                else:
                    self.log_with_timestamp(f"❌ HTTP error: {response.status_code}")
                    self.log_with_timestamp(f"📄 Error response: {response.text}")
                    return False, f"HTTP {response.status_code}"
                    
        except httpx.TimeoutException as e:
            elapsed = time.time() - self.start_time if self.start_time else 0
            self.log_with_timestamp(f"⏰ TIMEOUT after {elapsed:.2f} seconds: {e}")
            return False, f"Timeout after {elapsed:.2f}s"
            
        except httpx.ConnectError as e:
            self.log_with_timestamp(f"🔌 CONNECTION ERROR: {e}")
            return False, f"Connection error: {e}"
            
        except Exception as e:
            elapsed = time.time() - self.start_time if self.start_time else 0
            self.log_with_timestamp(f"❌ UNEXPECTED ERROR after {elapsed:.2f} seconds: {e}")
            return False, f"Error after {elapsed:.2f}s: {e}"
    
    async def test_orchestrator_health(self):
        """Test basic orchestrator connectivity"""
        self.log_with_timestamp("🏥 Testing orchestrator health")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.dashboard_url}/")  # Test dashboard
                self.log_with_timestamp(f"🏥 Dashboard health check status: {response.status_code}")
                dashboard_ok = response.status_code in [200, 405]  # 405 is expected for GET on POST endpoint
                
                # Also test orchestrator
                response = await client.get(f"{self.orchestrator_url}/")  # Test orchestrator  
                self.log_with_timestamp(f"🏥 Orchestrator health check status: {response.status_code}")
                orchestrator_ok = response.status_code in [200, 405]
                
                return dashboard_ok and orchestrator_ok
        except Exception as e:
            self.log_with_timestamp(f"🏥 Health check failed: {e}")
            return False
    
    async def test_confirmation_workflow(self):
        """Test the two-step confirmation workflow that UI uses"""
        self.log_with_timestamp("🔄 Testing full confirmation workflow")
        
        # Step 1: Initial claim extraction request
        self.log_with_timestamp("📋 Step 1: Sending initial claim extraction request")
        
        initial_request = {
            "message": f"process the claim for claim id {self.test_claim_id}",
            "sessionId": f"debug_workflow_{int(time.time())}",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                start_step1 = time.time()
                response1 = await client.post(f"{self.dashboard_url}/api/chat", json=initial_request)
                elapsed_step1 = time.time() - start_step1
                
                self.log_with_timestamp(f"📋 Step 1 completed in {elapsed_step1:.2f} seconds")
                self.log_with_timestamp(f"📋 Step 1 status: {response1.status_code}")
                
                if response1.status_code != 200:
                    self.log_with_timestamp(f"❌ Step 1 failed: {response1.text}")
                    return False, "Step 1 failed"
                
                # Wait a bit before confirmation
                await asyncio.sleep(2)
                
                # Step 2: Confirmation request
                self.log_with_timestamp("✅ Step 2: Sending confirmation 'yes'")
                
                confirmation_request = {
                    "message": "yes",
                    "sessionId": initial_request["sessionId"],  # Same session
                    "timestamp": datetime.now().isoformat()
                }
                
                start_step2 = time.time()
                response2 = await client.post(f"{self.dashboard_url}/api/chat", json=confirmation_request)
                elapsed_step2 = time.time() - start_step2
                
                total_elapsed = elapsed_step1 + elapsed_step2
                self.log_with_timestamp(f"✅ Step 2 completed in {elapsed_step2:.2f} seconds")
                self.log_with_timestamp(f"🎯 Total workflow time: {total_elapsed:.2f} seconds")
                self.log_with_timestamp(f"✅ Step 2 status: {response2.status_code}")
                
                if response2.status_code == 200:
                    response_data = response2.json()
                    self.log_with_timestamp(f"🎉 Final response preview: {str(response_data)[:300]}...")
                    return True, response_data
                else:
                    self.log_with_timestamp(f"❌ Step 2 failed: {response2.text}")
                    return False, f"Step 2 failed: {response2.status_code}"
                    
        except httpx.TimeoutException as e:
            self.log_with_timestamp(f"⏰ Workflow timeout: {e}")
            return False, f"Workflow timeout: {e}"
        except Exception as e:
            self.log_with_timestamp(f"❌ Workflow error: {e}")
            return False, f"Workflow error: {e}"
    
    async def run_comprehensive_debug(self):
        """Run all debug tests"""
        self.log_with_timestamp("🚀 Starting comprehensive UI timeout debugging")
        self.log_with_timestamp(f"🎯 Target Dashboard: {self.dashboard_url}")
        self.log_with_timestamp(f"🎯 Target Orchestrator: {self.orchestrator_url}")
        self.log_with_timestamp(f"🔍 Test claim: {self.test_claim_id}")
        self.log_with_timestamp("=" * 80)
        
        # Test 1: Basic connectivity
        self.log_with_timestamp("🔍 TEST 1: Basic Orchestrator Connectivity")
        health_ok = await self.test_orchestrator_health()
        if not health_ok:
            self.log_with_timestamp("❌ Basic connectivity failed - aborting further tests")
            return
        
        self.log_with_timestamp("✅ Basic connectivity OK")
        self.log_with_timestamp("=" * 80)
        
        # Test 2: Single request simulation
        self.log_with_timestamp("🔍 TEST 2: Single Request Simulation (Like UI)")
        success1, result1 = await self.test_ui_request_simulation()
        
        if success1:
            self.log_with_timestamp("✅ Single request test PASSED")
        else:
            self.log_with_timestamp(f"❌ Single request test FAILED: {result1}")
        
        self.log_with_timestamp("=" * 80)
        
        # Test 3: Full workflow simulation
        self.log_with_timestamp("🔍 TEST 3: Full Confirmation Workflow Simulation")
        success2, result2 = await self.test_confirmation_workflow()
        
        if success2:
            self.log_with_timestamp("✅ Full workflow test PASSED")
        else:
            self.log_with_timestamp(f"❌ Full workflow test FAILED: {result2}")
        
        self.log_with_timestamp("=" * 80)
        
        # Summary
        self.log_with_timestamp("📊 DEBUGGING SUMMARY:")
        self.log_with_timestamp(f"   Basic connectivity: {'✅ PASS' if health_ok else '❌ FAIL'}")
        self.log_with_timestamp(f"   Single request: {'✅ PASS' if success1 else '❌ FAIL'}")
        self.log_with_timestamp(f"   Full workflow: {'✅ PASS' if success2 else '❌ FAIL'}")
        
        if not success1 and not success2:
            self.log_with_timestamp("🚨 CRITICAL: Both single request and workflow failed!")
            self.log_with_timestamp("💡 RECOMMENDATION: Check FastAPI/Uvicorn timeout settings")
        elif success1 and not success2:
            self.log_with_timestamp("⚠️  Single requests work but workflow fails")
            self.log_with_timestamp("💡 RECOMMENDATION: Check session management or A2A timeout")
        elif not success1 and success2:
            self.log_with_timestamp("🤔 Workflow works but single request fails - unusual")
        else:
            self.log_with_timestamp("✅ All tests passed - timeout might be UI-specific")
            self.log_with_timestamp("💡 RECOMMENDATION: Check browser developer tools for client-side timeouts")

async def main():
    """Run the debug tests"""
    debugger = UITimeoutDebugger()
    await debugger.run_comprehensive_debug()

if __name__ == "__main__":
    print("🔧 UI Timeout Debugger")
    print("🎯 This script will test the exact request pattern that the UI uses")
    print("⏳ Waiting for orchestrator to be ready...")
    print()
    
    asyncio.run(main())
