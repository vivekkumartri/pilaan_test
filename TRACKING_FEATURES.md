# Tracking Features Documentation

## Overview

This enhanced version tracks:
1. **Response Time** - How long each question takes to answer
2. **Cursor Movements** - Mouse position tracking throughout the assessment

---

## 📊 Data Captured Per Question

### Response Timing Data
```json
{
  "q1": {
    "response_time_ms": 5420,
    "response_time_seconds": "5.42",
    "selected_option": "A",
    "timestamp": "2024-02-04T14:30:22.123456"
  }
}
```

### Cursor Movement Data
```json
{
  "q1": {
    "movements": [
      {"x": 450, "y": 320, "timestamp": 1707053422000},
      {"x": 455, "y": 325, "timestamp": 1707053422100},
      {"x": 460, "y": 330, "timestamp": 1707053422200}
    ],
    "total_movements": 3,
    "first_movement": {"x": 450, "y": 320, "timestamp": 1707053422000},
    "last_movement": {"x": 460, "y": 330, "timestamp": 1707053422200}
  }
}
```

### Overall Analytics
```json
{
  "analytics": {
    "total_time_ms": 54200,
    "total_time_seconds": "54.20",
    "total_time_minutes": "0.90",
    "average_time_per_question_seconds": "5.42",
    "total_cursor_movements": 150
  }
}
```

---

## 🔍 Cursor Statistics Calculated

The server automatically calculates:

1. **Total movements across all questions**
2. **Average movements per question**
3. **Question with most cursor activity**
4. **Question with least cursor activity**
5. **Distance traveled (in pixels)** per question
6. **Average distance per movement**

Example cursor statistics:
```json
{
  "cursor_statistics": {
    "total_questions_tracked": 10,
    "total_movements_all_questions": 1523,
    "average_movements_per_question": 152.3,
    "questions_with_most_movement": "q5",
    "questions_with_least_movement": "q2",
    "movement_details": {
      "q1": {
        "total_movements": 145,
        "total_distance_pixels": 2340.56,
        "average_distance_per_movement": 16.14
      }
    }
  }
}
```

---

## 🎯 What This Data Reveals

### Response Time Analysis
- **Fast responses** (<2 seconds): Confident/impulsive decisions
- **Medium responses** (2-10 seconds): Thoughtful consideration
- **Slow responses** (>10 seconds): Uncertainty or deep thinking

### Cursor Movement Analysis
- **High movement**: Hesitation, comparing options
- **Low movement**: Quick decision making
- **Distance traveled**: Level of engagement with options
- **Movement patterns**: Can reveal reading behavior

---

## 📁 Saved Data Structure

Each assessment saves to: `assessment_data/{user_id}_{timestamp}.json`

Complete file structure:
```json
{
  "user_id": "john_doe_1234567890",
  "user_name": "John Doe",
  "email_id": "john@example.com",
  "phone_number": "1234567890",
  "timestamp": "2024-02-04T14:30:22.123456",
  
  "responses": {
    "q1": "A",
    "q2": "B"
  },
  
  "response_timings": {
    "q1": {
      "response_time_ms": 5420,
      "response_time_seconds": "5.42",
      "selected_option": "A",
      "timestamp": "2024-02-04T14:30:22.123456"
    }
  },
  
  "cursor_movements": {
    "q1": {
      "movements": [...],
      "total_movements": 145,
      "first_movement": {...},
      "last_movement": {...}
    }
  },
  
  "analytics": {
    "total_time_ms": 54200,
    "total_time_seconds": "54.20",
    "total_time_minutes": "0.90",
    "average_time_per_question_seconds": "5.42",
    "total_cursor_movements": 1523
  },
  
  "cursor_statistics": {
    "total_questions_tracked": 10,
    "average_movements_per_question": 152.3,
    "questions_with_most_movement": "q5",
    "movement_details": {...}
  }
}
```

---

## 🔌 API Endpoints

### 1. Submit Assessment
```bash
POST /api/submit
```

Accepts tracking data and saves to server.

### 2. Get Detailed Analytics
```bash
GET /api/analytics/{user_id}
```

Returns comprehensive analytics including:
- User info
- Completion rate
- Timing analysis
- Cursor tracking stats
- Per-question details

Example response:
```json
{
  "user_info": {...},
  "completion": {
    "total_questions": 10,
    "answered_questions": 10,
    "completion_rate": "100.0%"
  },
  "timing": {...},
  "cursor_tracking": {...},
  "question_details": [...]
}
```

### 3. List All Assessments
```bash
GET /api/assessments
```

Returns summary of all assessments with key metrics.

### 4. Get Full Assessment Data
```bash
GET /api/assessment/{user_id}
```

Returns complete assessment data including all tracking info.

---

## 💡 Usage Examples

### View Analytics for a User
```bash
curl http://localhost:8000/api/analytics/john_doe_1234567890 | jq
```

### Check Cursor Activity
```bash
curl http://localhost:8000/api/assessment/john_doe_1234567890 | \
  jq '.cursor_statistics'
```

### Find Users with Longest Response Times
```bash
curl http://localhost:8000/api/assessments | \
  jq '.assessments | sort_by(.total_time_minutes) | reverse | .[0:5]'
```

---

## 🎨 Frontend Features

### Live Timer Display
- Shows elapsed time for current question in real-time
- Updates every 100ms
- Displayed in top-right corner during assessment

### Cursor Tracking Indicator
- Shows count of cursor movements at bottom
- Updates as user moves mouse
- Helps verify tracking is working

### Throttled Tracking
- Cursor positions captured every 100ms
- Prevents excessive data collection
- Balances accuracy with performance

---

## 🔒 Privacy Considerations

### What's Tracked
✓ Response times (how long to answer)
✓ Cursor positions (x, y coordinates)
✓ Timestamps for all events

### What's NOT Tracked
✗ Keystrokes or text input
✗ Other browser activity
✗ Personal browsing history
✗ Clicks outside the assessment

### Data Storage
- All data stored server-side only
- No browser downloads or local storage
- JSON files in secure directory
- Admin-only access to full data

---

## 📈 Analysis Ideas

### Behavioral Insights
1. **Decision Confidence**: Fast responses = more confident
2. **Engagement Level**: More movements = more engagement
3. **Comparison Behavior**: High movement = comparing options
4. **Certainty Patterns**: Consistent timing = consistent certainty

### Question Difficulty
- Questions with longer average times → harder questions
- Questions with more cursor movement → more complex options
- Can identify confusing or ambiguous questions

### User Patterns
- Some users consistently fast/slow
- Movement patterns may indicate reading style
- Can segment users by behavior type

---

## 🛠️ Technical Details

### Cursor Sampling Rate
- Default: 100ms (10 samples per second)
- Adjustable by changing `setTimeout` value
- Balance between accuracy and data size

### Timer Precision
- Millisecond precision using `Date.now()`
- Accurate to within 1-2ms
- Suitable for behavioral analysis

### Data Size
- Typical assessment: 50-200KB per user
- Cursor data is largest component
- Consider compression for long-term storage

---

## 🚀 Quick Start

1. **Use the tracking version:**
   ```bash
   python main_with_tracking.py
   ```

2. **Open browser:**
   ```
   http://localhost:8000
   ```

3. **View results:**
   ```bash
   # List all
   curl http://localhost:8000/api/assessments
   
   # Get analytics
   curl http://localhost:8000/api/analytics/{user_id}
   ```

---

## ⚙️ Configuration

### Adjust Cursor Sampling
In HTML, find this line:
```javascript
}, 100); // Capture every 100ms
```

Change to:
- `50` - More detailed (20 samples/sec)
- `200` - Less detailed (5 samples/sec)
- `500` - Minimal (2 samples/sec)

### Disable Cursor Tracking
Remove or comment out the cursor tracking `useEffect` in the HTML.

---

## 🎓 Best Practices

1. **Inform Users**: Let them know tracking is happening
2. **Secure Data**: Protect assessment files from unauthorized access
3. **Regular Cleanup**: Archive old assessments periodically
4. **Backup Data**: Keep backups of assessment files
5. **Privacy Policy**: Include tracking in your privacy policy

---

## 📊 Sample Analytics Output

```json
{
  "user_info": {
    "user_id": "john_doe_1234567890",
    "user_name": "John Doe",
    "email_id": "john@example.com",
    "timestamp": "2024-02-04T14:30:22.123456"
  },
  "completion": {
    "total_questions": 3,
    "answered_questions": 3,
    "completion_rate": "100.0%"
  },
  "timing": {
    "total_time_ms": 25680,
    "total_time_seconds": "25.68",
    "total_time_minutes": "0.43",
    "average_time_per_question_seconds": "8.56"
  },
  "cursor_tracking": {
    "total_questions_tracked": 3,
    "total_movements_all_questions": 342,
    "average_movements_per_question": 114.0,
    "questions_with_most_movement": "q2",
    "questions_with_least_movement": "q1"
  },
  "question_details": [
    {
      "question_id": "q1",
      "selected_option": "A",
      "timing": {
        "response_time_ms": 5420,
        "response_time_seconds": "5.42"
      },
      "cursor_activity": {
        "total_movements": 87,
        "has_movement_data": true
      }
    }
  ]
}
```
