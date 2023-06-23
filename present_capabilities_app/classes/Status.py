import json
import os.path


class Status:
    def __init__(self, name) -> None:
        self.name = name
        self.pointer = 0
        # print(f"Created status {name}")

    def saveStatus(self, position=None):
        self.pointer = position if position is not None else 0

        with open(f"statuses/{self.name}.json", "w") as f:
            json.dump({"checkpoint": self.pointer}, f)

    def loadStatus(self):
        if os.path.exists(f"statuses/{self.name}.json"):
            with open(f"statuses/{self.name}.json") as f:
                data = json.load(f)
                print(data)
                self.pointer = (
                    data["checkpoint"] if data["checkpoint"] is not None else 0
                )
        else:
            self.pointer = 0
