#!/usr/bin/env python3
"""Simple E2E test runner with minimal dependencies.

This script tests the complete MihenkAI workflow without docker-compose,
assuming services are already running or will be started separately.
"""
import requests
import json
import time
from typing import Optional, Dict, Any


def test_mihenkai_workflow():
    """Test MihenkAI evaluation workflow."""
    
    base_url = "http://localhost:8000"
    
    print("\n" + "="*60)
    print("MihenkAI Simple E2E Test")
    print("="*60)
    
    # Check if backend is running
    print("\n1. Checking if backend is running...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
        else:
            print(f"✗ Backend responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("  Make sure to run: docker-compose -f docker-compose.yml up -d")
        return False
    
    # Setup config
    print("\n2. Setting up configuration...")
    try:
        response = requests.post(
            f"{base_url}/config",
            json={
                "db_host": "db",
                "db_port": 5432,
                "db_user": "mihenkai_user",
                "db_password": "secure_password",
                "db_name": "mihenkai_db",
                "redis_host": "redis",
                "redis_port": 6379,
            },
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✓ Configuration setup successful")
        else:
            print(f"✗ Configuration setup got status {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"⚠ Configuration might already be set: {e}")
    
    # Create model configuration
    print("\n3. Creating model configuration...")
    model_id = None
    try:
        response = requests.post(
            f"{base_url}/models",
            json={
                "provider": "OpenAI",
                "model_name": "gpt-4",
                "api_key": "sk-test-key-e2e",
                "temperature": 0.7
            },
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            model_id = data.get('id')
            print(f"✓ Model created (ID: {model_id})")
        else:
            print(f"✗ Model creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Model creation error: {e}")
        return False
    
    if model_id is None:
        print("✗ Could not get model ID")
        return False
    
    # Create evaluation profile
    print("\n4. Creating evaluation profile...")
    profile_id = None
    try:
        response = requests.post(
            f"{base_url}/profiles",
            json={
                "name": "E2E Test Profile",
                "description": "Profile for E2E testing",
                "model_config_id": model_id,
                "single_weights": {
                    "faithfulness": 0.3,
                    "relevancy": 0.4,
                    "completeness": 0.3
                }
            },
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            profile_id = data.get('id')
            print(f"✓ Profile created (ID: {profile_id})")
        else:
            print(f"✗ Profile creation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Profile creation error: {e}")
        return False
    
    if profile_id is None:
        print("✗ Could not get profile ID")
        return False
    
    # Start evaluation
    print("\n5. Starting evaluation...")
    job_id = None
    try:
        response = requests.post(
            f"{base_url}/evaluate/single",
            json={
                "profile_id": profile_id,
                "prompt": "What is the capital of France?",
                "actual_response": "Paris is the capital of France, located in the north-central region of the country.",
                "retrieved_contexts": [
                    "Paris is the capital of France.",
                    "France is in Western Europe."
                ]
            },
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            job_id = data.get('job_id')
            print(f"✓ Evaluation started (Job: {job_id})")
        else:
            print(f"✗ Evaluation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Evaluation error: {e}")
        return False
    
    if job_id is None:
        print("✗ Could not get job ID")
        return False
    
    # Poll for results
    print(f"\n6. Polling for results (max 60 seconds)...")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < 60:
        try:
            response = requests.get(
                f"{base_url}/evaluate/{job_id}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status != last_status:
                    print(f"  Status: {status}")
                    last_status = status
                
                if status == "COMPLETED":
                    print("✓ Evaluation completed")
                    
                    # Display results
                    composite_score = data.get('composite_score')
                    print(f"\n  Results:")
                    print(f"    Composite Score: {composite_score:.2f}")
                    
                    metrics = data.get('metrics_breakdown', {})
                    if metrics:
                        print(f"    Metrics:")
                        for metric_name, metric_data in metrics.items():
                            if isinstance(metric_data, dict):
                                score = metric_data.get('score', 'N/A')
                                weight = metric_data.get('weight', 'N/A')
                                print(f"      - {metric_name}: {score:.2f} (weight: {weight})")
                            else:
                                print(f"      - {metric_name}: {metric_data}")
                    
                    # Verify score
                    if isinstance(composite_score, (int, float)) and 0 <= composite_score <= 100:
                        print(f"\n✓ Score is valid (0-100)")
                        return True
                    else:
                        print(f"\n✗ Invalid score: {composite_score}")
                        return False
                
                elif status == "FAILED":
                    error = data.get('error_message', 'Unknown error')
                    print(f"✗ Evaluation failed: {error}")
                    return False
                
                time.sleep(2)
            else:
                print(f"  Poll returned status {response.status_code}")
                time.sleep(2)
        except Exception as e:
            print(f"  Poll error: {e}")
            time.sleep(2)
    
    print("✗ Timeout waiting for evaluation to complete")
    return False


if __name__ == "__main__":
    print("\nDEBUG MODE: Test the evaluation workflow without docker")
    print("Make sure docker-compose services are running:")
    print("  docker-compose -f docker-compose.yml up -d")
    
    success = test_mihenkai_workflow()
    
    print("\n" + "="*60)
    if success:
        print("✓ E2E TEST PASSED")
    else:
        print("✗ E2E TEST FAILED")
    print("="*60)
