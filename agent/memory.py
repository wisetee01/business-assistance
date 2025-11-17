from typing import List, Dict

class ConversationMemory:
   
    def __init__(self, max_size: int = 10): 
        self.history: List[Dict[str, str]] = []
        self.max_size = max_size

    def add(self, user: str, assistant: str) -> None:
        self.history.append({"user": user, "assistant": assistant})
        if len(self.history) > self.max_size:
            self.history.pop(0)

    def get_recent(self) -> List[Dict[str, str]]:
        
        return self.history 

memory = ConversationMemory()
