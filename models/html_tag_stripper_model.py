from html.parser import HTMLParser


class HTMLTagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stripped_text = []

    def handle_data(self, data):
        self.stripped_text.append(data)