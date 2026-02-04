#!/usr/bin/env python3
"""
Assessment Data Analyzer
Analyzes response timing and cursor movement data from personality assessments
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys

DATA_DIR = Path("assessment_data")

def load_all_assessments() -> List[Dict]:
    """Load all assessment JSON files"""
    assessments = []
    if not DATA_DIR.exists():
        print(f"Error: {DATA_DIR} directory not found")
        return assessments
    
    for file in DATA_DIR.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assessments.append(data)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return assessments

def analyze_response_times(assessments: List[Dict]) -> Dict[str, Any]:
    """Analyze response time patterns"""
    all_times = []
    question_times = {}
    
    for assessment in assessments:
        timings = assessment.get('response_timings', {})
        for q_id, timing in timings.items():
            time_seconds = float(timing['response_time_seconds'])
            all_times.append(time_seconds)
            
            if q_id not in question_times:
                question_times[q_id] = []
            question_times[q_id].append(time_seconds)
    
    if not all_times:
        return {}
    
    # Calculate question difficulty (average time)
    question_difficulty = {}
    for q_id, times in question_times.items():
        question_difficulty[q_id] = {
            'average_time': round(statistics.mean(times), 2),
            'median_time': round(statistics.median(times), 2),
            'std_dev': round(statistics.stdev(times), 2) if len(times) > 1 else 0,
            'min_time': round(min(times), 2),
            'max_time': round(max(times), 2),
            'sample_size': len(times)
        }
    
    # Sort questions by difficulty (longest avg time)
    sorted_questions = sorted(
        question_difficulty.items(),
        key=lambda x: x[1]['average_time'],
        reverse=True
    )
    
    return {
        'overall': {
            'total_responses': len(all_times),
            'average_time': round(statistics.mean(all_times), 2),
            'median_time': round(statistics.median(all_times), 2),
            'std_dev': round(statistics.stdev(all_times), 2) if len(all_times) > 1 else 0,
            'min_time': round(min(all_times), 2),
            'max_time': round(max(all_times), 2)
        },
        'by_question': dict(question_difficulty),
        'difficulty_ranking': [
            {'question_id': q[0], **q[1]} 
            for q in sorted_questions[:10]  # Top 10 hardest
        ]
    }

def analyze_cursor_movements(assessments: List[Dict]) -> Dict[str, Any]:
    """Analyze cursor movement patterns"""
    all_movements = []
    question_movements = {}
    
    for assessment in assessments:
        cursor_data = assessment.get('cursor_movements', {})
        for q_id, movement_data in cursor_data.items():
            movement_count = movement_data.get('total_movements', 0)
            all_movements.append(movement_count)
            
            if q_id not in question_movements:
                question_movements[q_id] = []
            question_movements[q_id].append(movement_count)
    
    if not all_movements:
        return {}
    
    # Calculate question engagement (average cursor activity)
    question_engagement = {}
    for q_id, movements in question_movements.items():
        question_engagement[q_id] = {
            'average_movements': round(statistics.mean(movements), 2),
            'median_movements': round(statistics.median(movements), 2),
            'std_dev': round(statistics.stdev(movements), 2) if len(movements) > 1 else 0,
            'sample_size': len(movements)
        }
    
    # Sort questions by engagement (most cursor activity)
    sorted_engagement = sorted(
        question_engagement.items(),
        key=lambda x: x[1]['average_movements'],
        reverse=True
    )
    
    return {
        'overall': {
            'total_tracked': len(all_movements),
            'average_movements': round(statistics.mean(all_movements), 2),
            'median_movements': round(statistics.median(all_movements), 2),
            'std_dev': round(statistics.stdev(all_movements), 2) if len(all_movements) > 1 else 0
        },
        'by_question': dict(question_engagement),
        'engagement_ranking': [
            {'question_id': q[0], **q[1]} 
            for q in sorted_engagement[:10]  # Top 10 most engaging
        ]
    }

def analyze_user_patterns(assessments: List[Dict]) -> Dict[str, Any]:
    """Analyze individual user patterns"""
    users = []
    
    for assessment in assessments:
        analytics = assessment.get('analytics', {})
        cursor_stats = assessment.get('cursor_statistics', {})
        
        user_pattern = {
            'user_id': assessment.get('user_id'),
            'user_name': assessment.get('user_name'),
            'total_time_minutes': float(analytics.get('total_time_minutes', 0)),
            'avg_time_per_question': float(analytics.get('average_time_per_question_seconds', 0)),
            'total_cursor_movements': cursor_stats.get('total_movements_all_questions', 0),
            'avg_movements_per_question': cursor_stats.get('average_movements_per_question', 0),
            'completion_rate': assessment.get('answered_questions', 0) / assessment.get('total_questions', 1)
        }
        users.append(user_pattern)
    
    if not users:
        return {}
    
    # Categorize users
    avg_times = [u['avg_time_per_question'] for u in users if u['avg_time_per_question'] > 0]
    avg_movements = [u['avg_movements_per_question'] for u in users if u['avg_movements_per_question'] > 0]
    
    if avg_times:
        time_threshold = statistics.median(avg_times)
    else:
        time_threshold = 0
        
    if avg_movements:
        movement_threshold = statistics.median(avg_movements)
    else:
        movement_threshold = 0
    
    categorized = {
        'fast_decisive': [],      # Fast + Low movement
        'fast_exploratory': [],   # Fast + High movement
        'slow_decisive': [],      # Slow + Low movement
        'slow_exploratory': []    # Slow + High movement
    }
    
    for user in users:
        if user['avg_time_per_question'] == 0:
            continue
            
        is_fast = user['avg_time_per_question'] < time_threshold
        is_low_movement = user['avg_movements_per_question'] < movement_threshold
        
        if is_fast and is_low_movement:
            categorized['fast_decisive'].append(user)
        elif is_fast and not is_low_movement:
            categorized['fast_exploratory'].append(user)
        elif not is_fast and is_low_movement:
            categorized['slow_decisive'].append(user)
        else:
            categorized['slow_exploratory'].append(user)
    
    return {
        'total_users': len(users),
        'thresholds': {
            'time_median': round(time_threshold, 2),
            'movement_median': round(movement_threshold, 2)
        },
        'categories': {
            'fast_decisive': {
                'count': len(categorized['fast_decisive']),
                'description': 'Quick decision makers with minimal hesitation',
                'users': [u['user_name'] for u in categorized['fast_decisive'][:5]]
            },
            'fast_exploratory': {
                'count': len(categorized['fast_exploratory']),
                'description': 'Quick but thorough - reads all options fast',
                'users': [u['user_name'] for u in categorized['fast_exploratory'][:5]]
            },
            'slow_decisive': {
                'count': len(categorized['slow_decisive']),
                'description': 'Thoughtful and confident once decided',
                'users': [u['user_name'] for u in categorized['slow_decisive'][:5]]
            },
            'slow_exploratory': {
                'count': len(categorized['slow_exploratory']),
                'description': 'Careful consideration of all options',
                'users': [u['user_name'] for u in categorized['slow_exploratory'][:5]]
            }
        }
    }

def generate_report():
    """Generate comprehensive analysis report"""
    print("=" * 70)
    print("PERSONALITY ASSESSMENT - DATA ANALYSIS REPORT")
    print("=" * 70)
    print()
    
    # Load data
    print("Loading assessment data...")
    assessments = load_all_assessments()
    
    if not assessments:
        print("No assessment data found!")
        return
    
    print(f"Loaded {len(assessments)} assessments")
    print()
    
    # Response Time Analysis
    print("-" * 70)
    print("RESPONSE TIME ANALYSIS")
    print("-" * 70)
    time_analysis = analyze_response_times(assessments)
    if time_analysis:
        overall = time_analysis['overall']
        print(f"Total responses analyzed: {overall['total_responses']}")
        print(f"Average response time: {overall['average_time']}s")
        print(f"Median response time: {overall['median_time']}s")
        print(f"Range: {overall['min_time']}s - {overall['max_time']}s")
        print()
        print("Top 5 Most Difficult Questions (longest avg time):")
        for i, q in enumerate(time_analysis['difficulty_ranking'][:5], 1):
            print(f"  {i}. {q['question_id']}: {q['average_time']}s avg (σ={q['std_dev']})")
    print()
    
    # Cursor Movement Analysis
    print("-" * 70)
    print("CURSOR MOVEMENT ANALYSIS")
    print("-" * 70)
    cursor_analysis = analyze_cursor_movements(assessments)
    if cursor_analysis:
        overall = cursor_analysis['overall']
        print(f"Total questions tracked: {overall['total_tracked']}")
        print(f"Average movements per question: {overall['average_movements']}")
        print(f"Median movements: {overall['median_movements']}")
        print()
        print("Top 5 Most Engaging Questions (most cursor activity):")
        for i, q in enumerate(cursor_analysis['engagement_ranking'][:5], 1):
            print(f"  {i}. {q['question_id']}: {q['average_movements']} avg movements")
    print()
    
    # User Pattern Analysis
    print("-" * 70)
    print("USER BEHAVIOR PATTERNS")
    print("-" * 70)
    user_patterns = analyze_user_patterns(assessments)
    if user_patterns:
        print(f"Total users analyzed: {user_patterns['total_users']}")
        print()
        print("User Categories:")
        for category, data in user_patterns['categories'].items():
            print(f"\n  {category.replace('_', ' ').title()}: {data['count']} users")
            print(f"    {data['description']}")
            if data['users']:
                print(f"    Examples: {', '.join(data['users'])}")
    print()
    
    print("=" * 70)
    print("END OF REPORT")
    print("=" * 70)

if __name__ == "__main__":
    generate_report()
