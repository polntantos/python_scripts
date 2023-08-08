import click
from classes.RMLmapping import RMLmapping
from classes.VirtuosoWrapper import VirtuosoWrapper
from multiprocessing import Process, Queue
from rdflib import Graph

CONVERT_TYPES = {"auto": "Automatic", "manual": "Manual"}


@click.command()
@click.argument(
    "mode",
    type=click.Choice(CONVERT_TYPES.keys()),
    default="auto",
    # help="Deside whether to be prompted on choises about the conversion (Better for debugging)",
)
@click.argument(
    "mappingfile",
    type=click.Path(exists=False),
    required=0,
    # prompt="The path of the mapping file",
    # help="We need the mapping file to continue with the conversion of the database data to RDF",
)
@click.option(
    "--checkpoint",
    default=False,
    prompt="Continue where you left off",
    help="Continue where you left off",
)
@click.option(
    "--savetodb",
    default=False,
    prompt="Save to virtuoso db?",
    help="Choose whether to save your data to virtuoso or in a ttl file",
)
def start_conversion(mode, mappingfile, checkpoint, savetodb):
    mappingfile = (
        mappingfile
        if mappingfile is not None
        else "mappings/omikron44-supernova-mapping.ttl"
    )
    click.echo(f"{mode}, {mappingfile}, {checkpoint},{savetodb}")
    # exit()
    rmlMapping = RMLmapping(mappingfile, checkpoint=checkpoint)

    if mode == "manual":
        for key, triplesMap in enumerate(rmlMapping.mappings):
            print(f"{key}:{triplesMap.name}")
        user_input = input("Enter one or more numbers (separated by spaces): ")
        selected_numbers = user_input.split()
        print(selected_numbers)
    else:
        keys = []
        for key, triplesMap in enumerate(rmlMapping.mappings):
            print(f"{key}:{triplesMap.name}")
            keys.append(str(key))
        print("Auto mode will run all mappings")
        selected_numbers=",".join(keys)
    for key, mapping in enumerate(rmlMapping.mappings):
        if len(selected_numbers) != 0 and str(key) not in selected_numbers:
            continue

        if savetodb:
            virtuoso = VirtuosoWrapper()
        else:
            virtuoso = None

        rowsQueue = Queue()
        # print(mapping)
        dbProcess = Process(
            target=getDataFromLogicalTables,
            args=(
                mapping,
                rowsQueue,
            ),
            daemon=True,
        )

        conversionProcess = Process(
            target=convertDBrowsToGraph,
            args=(
                mapping,
                rowsQueue,
                virtuoso,
            ),
            daemon=True,
        )

        dbProcess.start()
        print("activating dbProcess")
        conversionProcess.start()
        print("activating conversion")
        dbProcess.join()
        conversionProcess.join(timeout=20)


def getDataFromLogicalTables(mapping, rowsQueue):
    for table in mapping.logicalTables:
        table.construct_table()

        while True:
            data = table.fetch_data()
            if len(data) < 1:
                print("put none data to queue")
                rowsQueue.put((None, None, None))
                break

            print(f"put {table.cursor} data to queue")
            rowsQueue.put((table.cursor, table.name, data))


def convertDBrowsToGraph(mapping, rowsQueue, virtuoso):
    print(f"Started conversion process for mapping {mapping.name}")
    while True:
        try:
            cursor, name, data = rowsQueue.get(timeout=1)
            print(f"cursor:{cursor}, name:{name},")
            g = Graph()
            print(f"Cursor at {cursor} for logical table {name}")
            if data is None and name is None and cursor is None:
                print(f"Exiting")
                break

            print("Processing Rows")
            for index, row in data.iterrows():
                # print(f"{index}:{row}")
                subjects = []
                for subjectMap in mapping.subjectMap:
                    subjectUri = subjectMap.materialize(row, g)
                    subjects.append(subjectUri)

                for subject in subjects:
                    for objectMap in mapping.mappings:
                        # print(f"{subject}")
                        objectMap.materialize(row, subject, g)
            # print("Got Here")
            if virtuoso != None:
                print(f"Conversion ended for {cursor}")
                virtuoso.save(g)
            else:
                print(f"Conversion ended for {cursor}")
                g.serialize(
                    format="turtle",
                    destination=f"rdfDumps/{mapping.name}-{cursor}.ttl",
                )
            mapping.save(cursor)

        except:
            continue  # Exit loop if process 1 has finished


if __name__ == "__main__":
    start_conversion()
