#!/usr/bin/env python3
"""
Test the Option B fix by running a real local evaluation.
This will verify that we create ONE evaluation with ALL responses.
"""

import asyncio
import aiohttp
import logging
import time
import json
import sys
import subprocess
import signal
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class OptionBTestRunner:
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8000"
    
    async def start_server(self):
        """Start the web server in background."""
        logger.info("🚀 Starting web server...")
        
        # Start server in background
        env = os.environ.copy()
        
        # Load environment variables from .env file
        env_path = Path("/home/todd/storybench/.env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
        
        self.server_process = subprocess.Popen([
            "/home/todd/storybench/venv-storybench/bin/python",
            "/home/todd/storybench/start_web_server.py"
        ], env=env, cwd="/home/todd/storybench")
        
        # Wait for server to start
        for i in range(30):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/health") as response:
                        if response.status == 200:
                            logger.info("✅ Server started successfully")
                            return True
            except Exception:
                pass
            await asyncio.sleep(1)
        
        logger.error("❌ Server failed to start")
        return False
    
    def stop_server(self):
        """Stop the web server."""
        if self.server_process:
            logger.info("🛑 Stopping web server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    async def get_database_counts(self):
        """Get current evaluation and response counts."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get evaluations count
                async with session.get(f"{self.base_url}/api/evaluations") as response:
                    evals_data = await response.json()
                    evals_count = len(evals_data.get('evaluations', []))
                
                # Get responses count (approximate via debug endpoint if available)
                try:
                    async with session.get(f"{self.base_url}/api/debug/responses-count") as response:
                        if response.status == 200:
                            responses_data = await response.json()
                            responses_count = responses_data.get('count', 0)
                        else:
                            responses_count = "unknown"
                except:
                    responses_count = "unknown"
                
                return evals_count, responses_count
        except Exception as e:
            logger.warning(f"Could not get database counts: {e}")
            return "unknown", "unknown"
    
    async def start_local_evaluation(self):
        """Start a local model evaluation to test Option B."""
        try:
            async with aiohttp.ClientSession() as session:
                # Start evaluation
                eval_data = {
                    "models": ["TestLocal"],  # This should match a configured local model
                    "sequences": ["FilmNarrative"],  # Standard sequence
                    "settings": {
                        "num_runs": 3  # This is key for testing Option B
                    }
                }
                
                async with session.post(f"{self.base_url}/api/local-models/start", 
                                      json=eval_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        evaluation_id = result.get("evaluation_id")
                        logger.info(f"✅ Started evaluation: {evaluation_id}")
                        return evaluation_id
                    else:
                        error = await response.text()
                        logger.error(f"❌ Failed to start evaluation: {error}")
                        return None
        except Exception as e:
            logger.error(f"❌ Error starting evaluation: {e}")
            return None
    
    async def monitor_evaluation(self, evaluation_id, timeout_seconds=180):
        """Monitor evaluation progress via SSE."""
        logger.info(f"👀 Monitoring evaluation {evaluation_id}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/local-models/status/{evaluation_id}"
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Could not connect to SSE stream: {response.status}")
                        return False
                    
                    start_time = time.time()
                    async for line in response.content:
                        if time.time() - start_time > timeout_seconds:
                            logger.warning(f"⏰ Monitoring timeout after {timeout_seconds}s")
                            break
                        
                        line = line.decode().strip()
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                status = data.get("status")
                                
                                if status == "completed":
                                    logger.info("🎉 Evaluation completed!")
                                    return True
                                elif status == "error":
                                    logger.error(f"❌ Evaluation failed: {data.get('message')}")
                                    return False
                                elif status == "progress":
                                    current = data.get("current_task", 0)
                                    total = data.get("total_tasks", 0)
                                    logger.info(f"📊 Progress: {current}/{total}")
                                
                            except json.JSONDecodeError:
                                pass
                    
                    logger.warning("⚠️  SSE stream ended without completion")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring evaluation: {e}")
            return False
    
    async def verify_option_b_results(self, evaluation_id):
        """Verify that Option B created the correct database structure."""
        logger.info("🔍 Verifying Option B results...")
        
        try:
            # Get evaluation details
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/evaluations/{evaluation_id}") as response:
                    if response.status != 200:
                        logger.error("❌ Could not fetch evaluation details")
                        return False
                    
                    eval_data = await response.json()
                    logger.info(f"📋 Evaluation {evaluation_id}:")
                    logger.info(f"   Status: {eval_data.get('status')}")
                    logger.info(f"   Total tasks: {eval_data.get('total_tasks')}")
                    logger.info(f"   Completed tasks: {eval_data.get('completed_tasks')}")
                    
                    # Check if we have the expected number of responses
                    expected_responses = 1 * 3 * 3  # 1 model × 3 prompts × 3 runs = 9
                    actual_responses = eval_data.get('completed_tasks', 0)
                    
                    if actual_responses == expected_responses:
                        logger.info(f"✅ Correct number of responses: {actual_responses}")
                        return True
                    else:
                        logger.error(f"❌ Wrong number of responses: expected {expected_responses}, got {actual_responses}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error verifying results: {e}")
            return False
    
    async def run_test(self):
        """Run the complete Option B test."""
        logger.info("🧪 Starting Option B Fix Test")
        
        try:
            # Start server
            if not await self.start_server():
                return False
            
            # Get initial database state
            initial_evals, initial_responses = await self.get_database_counts()
            logger.info(f"📊 Initial state: {initial_evals} evaluations, {initial_responses} responses")
            
            # Start evaluation
            evaluation_id = await self.start_local_evaluation()
            if not evaluation_id:
                return False
            
            # Monitor evaluation
            success = await self.monitor_evaluation(evaluation_id)
            if not success:
                return False
            
            # Verify results
            if not await self.verify_option_b_results(evaluation_id):
                return False
            
            # Get final database state
            final_evals, final_responses = await self.get_database_counts()
            logger.info(f"📊 Final state: {final_evals} evaluations, {final_responses} responses")
            
            # Check that we created exactly 1 new evaluation
            if isinstance(initial_evals, int) and isinstance(final_evals, int):
                new_evals = final_evals - initial_evals
                if new_evals == 1:
                    logger.info("✅ Created exactly 1 evaluation (Option B working!)")
                else:
                    logger.error(f"❌ Created {new_evals} evaluations (should be 1)")
                    return False
            
            logger.info("🎉 OPTION B TEST PASSED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
        finally:
            self.stop_server()

async def main():
    runner = OptionBTestRunner()
    success = await runner.run_test()
    
    if success:
        print("\n🎉 OPTION B FIX VERIFIED - Creates unified evaluations!")
        sys.exit(0)
    else:
        print("\n❌ OPTION B TEST FAILED - Check logs above")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
