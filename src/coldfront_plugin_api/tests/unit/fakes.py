FAKE_USERS = {
    "fake-user-1": {
        "username": "fake-user-1",
        "first_name": "fake",
        "last_name": "user 1",
        "email": "fake_user_1@example.com",
        "source": "Fake Source"
    }
}


class FakeUserSearch():
    def __init__(self, user_search_string, search_by, **kwargs):
        self.user_search_string = user_search_string

    def search(self):
        matches = []

        if match := FAKE_USERS.get(self.user_search_string):
            matches.append(match)

        return {
            "matches": matches
        }
