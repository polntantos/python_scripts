import json

file = "clusters/similar-brand-clusters.json"
with open(file=file) as f:
    brand_clusters = json.load(f)

action_bag = {"skip": [], "merge": [], "create": [], "delete": []}
for key, cluster in brand_clusters.items():
    candidate_brands = {}
    for i, brand in enumerate(cluster["brands"].items()):
        if brand[0] in cluster["valid_brand_names"]:
            print(f" {i} : {brand[0]} (valid)")
        else:
            print(f" {i} : {brand[0]}")

        candidate_brands[i] = brand

    options = {
        0: "skip",
        1: "merge_on_valid",
        2: "create_new",
        3: "delete_cluster",
        6: "exit",
    }
    action = None
    while action not in options.keys():
        user_choise = input(f"Choose what to do with the cluster {options}:")
        action = int(user_choise) if user_choise is not "" else 0

    print(options[action])
    # Save skip for cluster number
    if options[action] == "skip":
        action_bag["skip"].append(key)
        continue
    # Select one or more valid brands and assign the rest brands on them
    # If one of the valid brands is a parent of the others then you will be prompted to define the parent(s) and then their children
    elif options[action] == "merge_on_valid":
        merge_on_valid = {
            "brands_to_validate": [],
            "merging_array": [],
            "parent_of_brands": [],
        }
        input_selected_brands = input(
            "select brand(s) to validate (separated by spaces): "
        )
        selected_brands_number_input = input_selected_brands.split()
        # print([candidate_brands[int(i)] for i in selected_brands])
        for brand_key in selected_brands_number_input:
            merge_on_valid["brands_to_validate"].append(
                candidate_brands.pop(int(brand_key))
            )

        if len(merge_on_valid["brands_to_validate"]) > 1 and len(candidate_brands) > 0:
            for valid_brand in merge_on_valid["brands_to_validate"]:
                # valid_brand = candidate_brands.pop(int(i))
                for i, unverified in candidate_brands.items():
                    print(f"{i}:{unverified}")
                brands_to_merge = input(
                    f"Select brands to be connected to {valid_brand} (separated by spaces):"
                )
                brands_to_merge = brands_to_merge.split()
                for merging_brand_key in brands_to_merge:
                    merge_on_valid["merging_array"].append(
                        {
                            valid_brand[1]: candidate_brands.pop(
                                int(merging_brand_key)
                            )[1]
                        }
                    )
        elif (
            len(merge_on_valid["brands_to_validate"]) == 1 and len(candidate_brands) > 0
        ):
            for candidate_brand_key, candidate_brand in candidate_brands.items():
                merge_on_valid["merging_array"].append(
                    {merge_on_valid["brands_to_validate"][0][1]: candidate_brand[1]}
                )

        if len(merge_on_valid["brands_to_validate"]) > 1:
            yn = input(
                "Do the validating brands have a parent child relation between them?[y/N]:"
            )
            if yn == "y":
                for candidate_parent_key, candidate_parent_brand in enumerate(
                    merge_on_valid["brands_to_validate"]
                ):
                    print(f"{candidate_parent_key} : {candidate_parent_brand[0]}")
                selected_parent = input("select the parent:")
                merge_on_valid["parent_of_brands"].append(
                    merge_on_valid["brands_to_validate"][int(selected_parent)]
                )
        action_bag["merge"].append({key: merge_on_valid})
        print(action_bag)
        # exit()
    # Create a new brand to assign all or some of the clustered brands
    elif options[action] == "create_new":
        input_selected_brands = input(
            "select brand(s) to tie to new brand (separated by spaces): "
        )
        selected_brands = input_selected_brands.split()
        print([candidate_brands[int(i)] for i in selected_brands])
    # Delete part or the whole cluster
    elif options[action] == "delete_cluster":
        pass
    else:
        break

print("Saving actions")
## Save actions here
with open("file-actions.json", "w") as f:
    json.dump(action_bag, f)
print("Exiting")
