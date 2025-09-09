#!/usr/bin/env python3
"""Check current processing steps"""

import requests
import time

def check_steps():
    time.sleep(2)  # Wait for processing
    
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    
    steps_count = len(data.get('steps', []))
    active_sessions = data.get('active_sessions', 0)
    
    print(f'Steps after processing: {steps_count}')
    print(f'Active sessions: {active_sessions}')
    
    steps = data.get('steps', [])
    if steps:
        print('First 3 steps:')
        for i, step in enumerate(steps[:3]):
            title = step.get('title', 'No title')
            status = 'completed' if step.get('completed_at') else 'active' if step.get('started_at') else 'pending'
            print(f'  {i+1}. {title} - {status}')

if __name__ == "__main__":
    check_steps()
