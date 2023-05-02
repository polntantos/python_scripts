import json


class Status:
    def __init__(self, rmlMapping) -> None:
        self.rmlMapping = rmlMapping
        self.status = {}

    def saveStatus(self, logicalTableName=None, position=None):
        tableStats = {}

        for mapping in self.rmlMapping.mappings:
            tripleMapStats = {}
            # print(mapping.name)
            for logicalTable in mapping.logicalTables:
                tripleMapStats[logicalTable.name] = logicalTable.cursor
                if (
                    logicalTableName != None
                    and position != None
                    and logicalTable.name == logicalTableName
                ):
                    print(f"Saving table {logicalTable.name} at cursor {position}")
                    tableStats[logicalTableName] = position

            tableStats[mapping.name.toPython()] = tripleMapStats

        # print(tableStats)
        self.status = tableStats

        with open("statuses/status.json", "w") as f:
            json.dump(tableStats, f)

    def loadStatus(self):
        with open("statuses/status.json") as f:
            data = json.load(f)
            self.status = data
