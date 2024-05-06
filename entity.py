class Question:
    def __init__(self, id, content, question_type, chat_id):
        self.id = id
        self.content = content
        self.type = question_type
        self.chat_id = chat_id

class Chat:
    def __init__(self, id, title):
        self.id = id
        self.title = title
