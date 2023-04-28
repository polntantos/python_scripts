import json


class Status:
    def __init__(self, rmlMapping) -> None:
        self.rmlMapping = rmlMapping
        self.status = {}

    def saveStatus(self):
        tableStats = {}

        for mapping in self.rmlMapping.mappings:
            tripleMapStats = {}
            # print(mapping.name)
            for logicalTable in mapping.logicalTables:
                # print(logicalTable.name)
                tripleMapStats[logicalTable.name] = logicalTable.cursor
            tableStats[mapping.name] = tripleMapStats

        # print(tableStats)
        self.status = tableStats

        with open("statuses/status.json", "w") as f:
            json.dump(tableStats, f)

    def loadStatus(self):
        with open("statuses/status.json") as f:
            data = json.load(f)
            self.status = data
