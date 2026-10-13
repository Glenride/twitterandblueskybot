{
  "posts": [],
  "replies": [],
  "dms": [],
  "rate_policy": {
    "min_interval_minutes": 15,
    "daily_max": {
      "tweets": 80,
      "dms": 120
    }
  },
  "alert_webhook": {
    "url": "https://your-worker.example.com/alerts",
    "secret": "super-secret-token",
    "retry_policy": {
      "retries": 3,
      "backoff_seconds": 60
    }
  }
}