import json


class Status:
    def __init__(self, rmlMapping) -> None:
        self.rmlMapping = rmlMapping
        self.status = {}

    def saveStatus(self, logicalTableName=None, position=None):
        tableStats = {}

        for mapping in self.rmlMapping.mappings:
            tripleMapStats = {}

            for logicalTable in mapping.logicalTables:
                tripleMapStats[logicalTable.name] = logicalTable.cursor

                if (
                    logicalTableName != None
                    and position != None
                    and logicalTable.name == logicalTableName
                ):
                    print(f"Saving table {logicalTableName} at cursor {position}")
                    tableStats[mapping.name.toPython()][logicalTableName] = position
                else:
                    tableStats[mapping.name.toPython()] = tripleMapStats

        # print(tableStats)
        self.status = tableStats

        with open("statuses/status.json", "w") as f:
            json.dump(tableStats, f)

    def loadStatus(self):
        with open("statuses/status.json") as f:
            data = json.load(f)
            self.status = data
