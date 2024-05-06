
from entity import Chat, Question

class ChatRepository:
    def __init__(self):
        self.chats = []
        self.next_id = 1

    def add_chat(self, title):
        chat = Chat(self.next_id, title)
        self.chats.append(chat)
        self.next_id += 1
        return chat.id

    def get_chat_by_id(self, chat_id):
        for chat in self.chats:
            if chat.id == chat_id:
                return chat
        return None

    def get_all_chats(self):
        return self.chats

    def delete_chat(self, chat_id):
        self.chats = [chat for chat in self.chats if chat.id != chat_id]



class QuestionRepository:
    def __init__(self):
        self.questions = []
        self.next_id = 1

    def add_question(self, content, question_type, chat_id):
        question = Question(self.next_id, content, question_type, chat_id)
        self.questions.append(question)
        self.next_id += 1
        return question.id

    def get_questions_by_chat_id(self, chat_id):
        return [question for question in self.questions if question.chat_id == chat_id]

    # Other methods remain unchanged
