#!/usr/bin/env python3
"""End-to-end test for MihenkAI using docker-compose.

This script:
1. Starts docker-compose services
2. Waits for services to be healthy
3. Performs a complete evaluation workflow
4. Verifies results
"""
import requests
import time
import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional


# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds per request
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds


class MihenkAIE2ETester:
    """End-to-end tester for MihenkAI."""
    
    def __init__(self, base_url: str = BASE_URL):
        """Initialize the tester."""
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def health_check(self) -> bool:
        """Check if backend is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def wait_for_service(self, max_retries: int = MAX_RETRIES) -> bool:
        """Wait for service to be healthy."""
        print("Waiting for backend service to be ready...")
        for attempt in range(max_retries):
            if self.health_check():
                print("✓ Backend service is ready")
                return True
            print(f"Attempt {attempt + 1}/{max_retries} - Service not ready yet...")
            time.sleep(RETRY_DELAY)
        print("✗ Backend service failed to start")
        return False
    
    def setup_config(self) -> bool:
        """Setup initial configuration."""
        print("\n1. Setting up configuration...")
        try:
            response = self.session.post(
                f"{self.base_url}/config",
                json={
                    "db_host": "db",
                    "db_port": 5432,
                    "db_user": "mihenkai_user",
                    "db_password": "secure_password",
                    "db_name": "mihenkai_db",
                    "redis_host": "redis",
                    "redis_port": 6379,
                },
                timeout=TIMEOUT
            )
            if response.status_code in [200, 201]:
                print("✓ Configuration setup successful")
                return True
            else:
                print(f"✗ Configuration setup failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Configuration setup error: {e}")
            return False
    
    def create_model_config(self) -> Optional[int]:
        """Create a model configuration."""
        print("\n2. Creating model configuration...")
        try:
            response = self.session.post(
                f"{self.base_url}/models",
                json={
                    "provider": "OpenAI",
                    "model_name": "gpt-4",
                    "api_key": "sk-test-key-for-e2e",
                    "temperature": 0.7
                },
                timeout=TIMEOUT
            )
            if response.status_code in [200, 201]:
                data = response.json()
                model_id = data.get('id')
                print(f"✓ Model configuration created (ID: {model_id})")
                return model_id
            else:
                print(f"✗ Model creation failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Model creation error: {e}")
            return None
    
    def create_evaluation_profile(self, model_id: int) -> Optional[int]:
        """Create an evaluation profile."""
        print("\n3. Creating evaluation profile...")
        try:
            response = self.session.post(
                f"{self.base_url}/profiles",
                json={
                    "name": "E2E Test Profile",
                    "description": "Profile for E2E testing",
                    "model_config_id": model_id,
                    "single_weights": {
                        "faithfulness": 0.3,
                        "relevancy": 0.4,
                        "completeness": 0.3
                    },
                    "conversational_weights": {
                        "faithfulness": 0.25,
                        "relevancy": 0.25,
                        "completeness": 0.25,
                        "knowledge_retention": 0.25
                    }
                },
                timeout=TIMEOUT
            )
            if response.status_code in [200, 201]:
                data = response.json()
                profile_id = data.get('id')
                print(f"✓ Evaluation profile created (ID: {profile_id})")
                return profile_id
            else:
                print(f"✗ Profile creation failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Profile creation error: {e}")
            return None
    
    def start_single_evaluation(self, profile_id: int) -> Optional[str]:
        """Start a single evaluation."""
        print("\n4. Starting single evaluation...")
        try:
            response = self.session.post(
                f"{self.base_url}/evaluate/single",
                json={
                    "profile_id": profile_id,
                    "prompt": "What is the capital of France?",
                    "actual_response": "The capital of France is Paris, a major city in Western Europe known for its art, museums, and landmarks.",
                    "retrieved_contexts": [
                        "Paris is the capital and most populous city of France.",
                        "France is a country in Western Europe with Paris as its capital."
                    ]
                },
                timeout=TIMEOUT
            )
            if response.status_code in [200, 201]:
                data = response.json()
                job_id = data.get('job_id')
                print(f"✓ Evaluation started (Job ID: {job_id})")
                return job_id
            else:
                print(f"✗ Evaluation start failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Evaluation start error: {e}")
            return None
    
    def poll_job_status(self, job_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
        """Poll job status until completion."""
        print(f"\n5. Polling job status (max {max_wait}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/evaluate/{job_id}",
                    timeout=TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    print(f"  Job status: {status}")
                    
                    if status == "COMPLETED":
                        print("✓ Evaluation completed")
                        return data
                    elif status == "FAILED":
                        print(f"✗ Evaluation failed: {data.get('error_message')}")
                        return None
                    
                    time.sleep(2)  # Wait before next poll
                else:
                    print(f"  Poll failed: {response.status_code}")
                    time.sleep(2)
            except Exception as e:
                print(f"  Poll error: {e}")
                time.sleep(2)
        
        print("✗ Job polling timeout")
        return None
    
    def run_workflow(self) -> bool:
        """Run the complete E2E workflow."""
        print("\n" + "="*60)
        print("MihenkAI End-to-End Test Workflow")
        print("="*60)
        
        # Step 1: Wait for service
        if not self.wait_for_service():
            return False
        
        # Step 2: Setup config
        if not self.setup_config():
            return False
        
        # Step 3: Create model
        model_id = self.create_model_config()
        if model_id is None:
            return False
        
        # Step 4: Create profile
        profile_id = self.create_evaluation_profile(model_id)
        if profile_id is None:
            return False
        
        # Step 5: Start evaluation
        job_id = self.start_single_evaluation(profile_id)
        if job_id is None:
            return False
        
        # Step 6: Poll results
        result = self.poll_job_status(job_id)
        if result is None:
            return False
        
        # Step 7: Verify results
        print("\n6. Verifying results...")
        composite_score = result.get('composite_score')
        metrics = result.get('metrics_breakdown', {})
        
        print(f"\nResults:")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {result.get('status')}")
        print(f"  Composite Score: {composite_score}")
        print(f"  Metrics:")
        for metric, values in metrics.items():
            if isinstance(values, dict):
                print(f"    - {metric}: {values.get('score', 'N/A')} (weight: {values.get('weight', 'N/A')})")
            else:
                print(f"    - {metric}: {values}")
        
        # Verify composite score is valid
        if isinstance(composite_score, (int, float)) and 0 <= composite_score <= 100:
            print("\n✓ Composite score is valid (0-100)")
        else:
            print(f"\n✗ Invalid composite score: {composite_score}")
            return False
        
        print("\n" + "="*60)
        print("✓ End-to-End Test PASSED")
        print("="*60)
        return True


def start_docker_compose() -> bool:
    """Start docker-compose services."""
    print("\nStarting docker-compose services...")
    try:
        # Build images
        print("Building Docker images...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.yml", "build"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"✗ Docker build failed: {result.stderr.decode()}")
            return False
        
        # Start services
        print("Starting services...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.yml", "up", "-d"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"✗ Docker compose up failed: {result.stderr.decode()}")
            return False
        
        print("✓ Docker services started")
        return True
    except Exception as e:
        print(f"✗ Docker compose error: {e}")
        return False


def stop_docker_compose() -> bool:
    """Stop docker-compose services."""
    print("\nStopping docker-compose services...")
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.yml", "down"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Docker services stopped")
            return True
        else:
            print(f"✗ Failed to stop services: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"✗ Docker compose error: {e}")
        return False


def main():
    """Main entry point."""
    try:
        # Start services
        if not start_docker_compose():
            sys.exit(1)
        
        # Wait for services to stabilize
        print("Waiting for services to stabilize...")
        time.sleep(5)
        
        # Run E2E test
        tester = MihenkAIE2ETester()
        success = tester.run_workflow()
        
        # Cleanup
        if "--keep-running" not in sys.argv:
            time.sleep(2)
            stop_docker_compose()
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        stop_docker_compose()
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        stop_docker_compose()
        sys.exit(1)


if __name__ == "__main__":
    main()
