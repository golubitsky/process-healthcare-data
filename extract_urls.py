import ijson

import sys
import collections


def is_matching(value):
    l = value.lower()
    return ("new york" in l or " ny " in l) and "ppo" in l


def with_dash(ein):
    index = 2
    return ein[:index] + "-" + ein[index:]


def extract_urls(file_path):
    results = {}

    with open(file_path, "r") as file:
        for reporting_structure in ijson.items(file, "reporting_structure.item"):
            for file in reporting_structure["in_network_files"]:
                if "NY_" in file["location"]:
                    representative_plan = None
                    is_ppo_plan_name_found = "no ppo found"

                    for plan in reporting_structure["reporting_plans"]:
                        # Heuristic: assume that a PPO will have 'ppo' in its name.
                        if "ppo" in plan["plan_name"].lower():
                            representative_plan = plan
                            is_ppo_plan_name_found = "   ppo found"

                            # To use the search tool, we need a plan with an EIN.
                            if plan["plan_id_type"] == "EIN":
                                break

                    if not representative_plan:
                        # There are no PPOs, but at least maybe there's a plan with an EIN.
                        for plan in reporting_structure["reporting_plans"]:
                            if plan["plan_id_type"] == "EIN":
                                representative_plan = plan
                                break
                    
                    if not representative_plan:
                        # There are no PPOs and there are no EIN identifiers.
                        representative_plan = reporting_structure["reporting_plans"][0]

                    if file["location"] not in results:
                        results[file["location"]] = {
                            "hint": is_ppo_plan_name_found,
                            "example_ein": with_dash(representative_plan["plan_id"]),
                            "plan": representative_plan["plan_name"],
                        }

        ordered = collections.OrderedDict(sorted(results.items()))
        for url, data in ordered.items():
            print(data["example_ein"], data["hint"], url)


if __name__ == "__main__":
    result_urls = extract_urls(sys.argv[1])
