from collections import defaultdict
import time
from typing import Dict, List

class RateLimiter:
    def __init__(self, max_commands: int = 10, time_window: int = 5, timeout_duration: int = 30):
        self.max_commands = max_commands
        self.time_window = time_window
        self.timeout_duration = timeout_duration
        self.command_history: Dict[int, List[float]] = defaultdict(list)
        self.timeouts: Dict[int, float] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        current_time = time.time()
        
        # Check if user is in timeout
        if user_id in self.timeouts:
            if current_time < self.timeouts[user_id]:
                return True
            else:
                del self.timeouts[user_id]
                self.command_history[user_id] = []
                return False

        # Clean old commands outside the time window
        self.command_history[user_id] = [
            cmd_time for cmd_time in self.command_history[user_id]
            if current_time - cmd_time <= self.time_window
        ]

        # Add current command
        self.command_history[user_id].append(current_time)

        # Check if user has exceeded rate limit
        if len(self.command_history[user_id]) > self.max_commands:
            self.timeouts[user_id] = current_time + self.timeout_duration
            return True

        return False

    def get_timeout_remaining(self, user_id: int) -> float:
        if user_id in self.timeouts:
            remaining = self.timeouts[user_id] - time.time()
            return max(0, remaining)
        return 0 