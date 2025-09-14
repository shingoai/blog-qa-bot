import json
import os
from datetime import datetime
from typing import List, Dict
from collections import Counter
import pandas as pd

class QuestionLogger:
    def __init__(self, log_file: str = "question_logs.json"):
        self.log_file = log_file
        self.logs = self._load_logs()
    
    def _load_logs(self) -> List[Dict]:
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_logs(self):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
    
    def log_question(self, question: str, answer: str, urls: List[str] = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "urls": urls or [],
            "id": len(self.logs) + 1
        }
        
        self.logs.append(log_entry)
        self._save_logs()
        
        return log_entry
    
    def get_all_logs(self) -> List[Dict]:
        return self.logs
    
    def get_recent_logs(self, n: int = 10) -> List[Dict]:
        return self.logs[-n:] if self.logs else []
    
    def get_frequent_questions(self, n: int = 10) -> List[Dict]:
        if not self.logs:
            return []
        
        questions = [log['question'] for log in self.logs]
        
        question_counts = Counter(questions)
        
        frequent = []
        for question, count in question_counts.most_common(n):
            frequent.append({
                "question": question,
                "count": count,
                "percentage": (count / len(self.logs)) * 100
            })
        
        return frequent
    
    def export_to_csv(self, filename: str = "question_logs.csv"):
        if not self.logs:
            return None
        
        df = pd.DataFrame(self.logs)
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    def search_logs(self, keyword: str) -> List[Dict]:
        keyword_lower = keyword.lower()
        results = []
        
        for log in self.logs:
            if (keyword_lower in log['question'].lower() or 
                keyword_lower in log['answer'].lower()):
                results.append(log)
        
        return results
    
    def get_stats(self) -> Dict:
        if not self.logs:
            return {
                "total_questions": 0,
                "unique_questions": 0,
                "avg_questions_per_day": 0
            }
        
        unique_questions = len(set([log['question'] for log in self.logs]))
        
        if self.logs:
            first_date = datetime.fromisoformat(self.logs[0]['timestamp'])
            last_date = datetime.fromisoformat(self.logs[-1]['timestamp'])
            days_diff = (last_date - first_date).days + 1
            avg_per_day = len(self.logs) / days_diff if days_diff > 0 else len(self.logs)
        else:
            avg_per_day = 0
        
        return {
            "total_questions": len(self.logs),
            "unique_questions": unique_questions,
            "avg_questions_per_day": round(avg_per_day, 2)
        }