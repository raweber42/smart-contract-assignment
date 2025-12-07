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
        else:
            # Default fallback
            return {
                "teacher_duration": 0,
                "student_duration": 0,
                "raw_json": {}
            }
