


class EventHub:
    def __init__(self):
        self._subscribers = []

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def notify(self, event):
        for subscriber in self._subscribers:
            subscriber(event)
