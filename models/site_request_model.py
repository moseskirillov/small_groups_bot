class SiteRequest:
    def __init__(self, date, name, surname, age, city, email, phone, group):
        self.date = date
        self.name = name
        self.surname = surname
        self.age = age
        self.city = city
        self.email = email
        self.phone = phone
        self.group = group

    def to_list(self):
        return [str(self.date), str(self.name), str(self.surname), str(self.age), str(self.city),
                str(self.email), str(self.phone), str(self.group)]
