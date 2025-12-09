import random

class Oracle:
    def __init__(self):
        self.scenario = "happy_path" # Default

    def set_scenario(self, scenario_key):
        self.scenario = scenario_key

    def get_meeting_data(self):
        # Simulating Google Meet API response
        # Returns duration in minutes
        
        if self.scenario == "happy_path":
            return {
                "teacher_duration": 60,
                "student_duration": 60,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": 3600},
                        {"email": "student@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "student_no_show":
            return {
                "teacher_duration": 60,
                "student_duration": 0,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "teacher_no_show":
            return {
                "teacher_duration": 0,
                "student_duration": 60,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "student@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "random":
            t_dur = random.randint(0, 60)
            s_dur = random.randint(0, 60)
            return {
                "teacher_duration": t_dur,
                "student_duration": s_dur,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": t_dur * 60},
                        {"email": "student@uni.com", "durationSeconds": s_dur * 60}
                    ]
                }
            }
        else:
            # Default fallback
            return {
                "teacher_duration": 0,
                "student_duration": 0,
                "raw_json": {}
            }
