

class AgioApiClient(AgioApiClientBase):
    def __init__(self):
        self.users = UsersNameSpace()
        self.pipelines = PipelinesNameSpace()
        self.studios = StudiosNameSpace()
        self.track = TrackNameSpace()


