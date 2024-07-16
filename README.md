## Overview

This repository contains a solution to the challenge described at [serif-health/takehome](https://github.com/serif-health/takehome). Please refer to their README.md for more information on the purpose of this repository.

## Solution

Cross-referencing the 50 URLs containing "NY" with information from the search tool (manually), we get **15 URLs**, listed in `urls_corresponding_to_anthems_ppo_in_new_york_state.txt`.

The intermediate results are saved in `intermediate_output_from_script.txt`, annotated at the end of each row with cross-references using the search tool.

For more information, see the sections "Explanation and Strategy" and "Performance" below.

For potential improvements, see "Notable Edge Cases and Possible Extension Ideas" below.

## Install

1. Ensure you have Python 3.12.3 installed. Download it [here](https://www.python.org/downloads).
2. From the project root, install dependencies using:

```
pip3 install -r requirements.txt`
```

## Run

```sh
python3 extract_urls.py 2024-07-01_anthem_index.json
```

## Difficulty in Identifying a Consistent MRF Naming Convention

According to the [CMS](https://www.cms.gov/healthplan-price-transparency/resources/technical-clarification), "The individual in-network rate files linked to the Table of Contents file need not follow a defined naming convention". Discussions, such as [this one](https://github.com/CMSgov/price-transparency-guide/discussions/619), also mention inconsistent or unspecified file naming conventions, particularly for Anthem.

## Explanation and Strategy

We have three sources of information:

1.  In each `reporting_structure` element, a list of `reporting_plans` that have pricing data across multiple MRFs; most plans are identified with an EIN.
2.  In each `reporting_structure` element, a list of `in_network_files` containing URLs of MRFs corresponding to the list of plans in the same `reporting_structure` element.
3.  Separately, a UI [MRF search tool](https://www.anthem.com/machine-readable-file/search/) provided by Anthem; we can search by EIN.

### First Approach: Identify Relevant Plans First

The initial approach was:

```
for each reporting_structure:
  if any of `reporting_plans` can be identified as PPO and New York:
    examine the corresponding `in_network_files`
```

This approach was challenging due to the lack of structured data to identify the plan as such. Searching for 'ny' or 'new york' and 'ppo' in `reporting_plan['plan_name']` was not reliable. Moreover, identifying the correct URLs remained problematic.

### Using the Hint about Anthem vs. Highmark

Inspection of `description` in `in_network_files` revealed that while many descriptions referenced 'new york' and 'ppo', they often also mentioned 'highmark'. Anthem and Highmark are not the same. Anthem is the focus, while Highmark operates under different BCBS companies, [per BCBS](https://www.bcbs.com/bcbs-companies-and-licensees).

Thus, URLs with descriptions referencing 'highmark' were ruled out as they apply to Highmark, not Anthem.

### Second Approach: Identify Relevant URLs First

The revised approach was:

```
for each reporting_structure:
  if any of the `in_network_files` URLs contain 'NY'
    examine the corresponding `reporting_plans` for evidence that _any one of them_ is a PPO
```

This led to identifying 50 URLs containing "NY", all having a consistent `description` of "In-Network Negotiated Rates Files", which seemed promising.

### Hypothesis on Anthem's MRF Naming Convention

These 50 URLs follow a pattern. Here are two representative examples:

1. NY_PPPNMED0001.json.gz
2. NY_GGHAMEDAP33_08_09.json.gz

A potential naming convention might be (underscores omitted for brevity):

1. 2 chars: State Abbreviation (e.g., NY for New York).
2. 4 chars: Plan/Region Code (e.g., GGHA, HXPX, HYRE for PPOs).
3. 3 chars: Service Type (always MED, possibly for Medical).
4. 4 chars: Sequence Number or Identifier (e.g., 0001 or AP33).
5. 2 chars (optional): Index of this MRF (e.g., 01).
6. 2 chars (optional): Total number of MRF files (e.g., 09).

Further clarity on the plan/region code and sequence number would be helpful.

### Heuristic to Identify PPOs

Using the Anthem Search Tool with EINs from the 50 URLs containing "NY", we verify which URLs pertain to PPOs.

The tool clearly differentiates between PPO, EPO, FFS, POS, etc., in the MRF filenames visible on the UI. Note that these differ from the actual filenames!

For example:

- PPO
  - Example EIN: 37-1441668
  - Example file name NY_GGHAMEDAP33_01_09.json.gz appears as "NY_PPO_GGHAMEDAP33_01_09.json.gz" on the UI
- EPO
  - Example EIN: 37-1441668
  - Example file name NY_GZHYMEDAP36.json.gz appears as "NY_EPO_GZHYMEDAP36.json.gz" on the UI
- Highmark files follow a different convention altogether
  - Identified in the table of contents file using `description` field contains "highmark"
  - Example EIN: 85-4347090
  - Example file name: 2024-07_800_72A0_in-network-rates_01_of_02.json.gz appears as "2024-07_NY_72A0_in-network-rates_01_of_02.json.gz" on the UI
    - Since the file name doesn't contain "NY\_" we won't have false positives.

### Notable edge cases and possible extension idea

- False negative using the heuristic
  - Using EIN 87-2928230 the MRF https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/NY_JBDTMED0000.json.gz appears as "NY_PPO_JBDTMED0000.json.gz" in the tool. This MRF contains PPO data according to the tool, although it has no corresponding PPO plans using the heuristic in extract_urls.py.
  - See "Possible future extension" below
- False negative using the heuristic
  - For EIN 87-2928230, the same MRF file can be referenced by the tool as both PPO and EPO across multiple EINs:
    - The URL https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/NY_HXNWMED0000.json.gz appears differently in the UI across two EINs:
      - EIN 87-2928230: appears as "NY_PPO_HXNWMED0000.json.gz" in the UI (not found using the heuristic, causing the file to be manually added to the final result)
      - EIN 57-1166714: appears as "NY_EPO_HXNWMED0000.json.gz" in the UI
    - **Possible future extension**
      - Exhaustively cross-reference _all_ EINs corresponding to an NY URL.
      - Alternatively, learn more about Anthem's MRF naming convention.
- False positive using the heuristic
  - For EIN 13-3680053, both NY_HXPYMED0004.json.gz (EPO according to the tool) and NY_HXPXMED0009.json.gz (PPO according to the tool) are referenced. NY_HXPYMED0004.json.gz has to be ruled out manually using the tool.
- File Appearing as Both PPO and EPO
  - For EIN 38-4042589 the file https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/NY_GZHYMEDAP36.json.gz appears as both "NY_EPO_GZHYMEDAP36.json.gz" and "NY_PPO_GZHYMEDAP36.json.gz" in the UI
    - **Hypothesis**: This MRF may contain both PPO and EPO pricing data.

## Performance

### Human

It took me about an hour to figure out how to load the large file, use the Python library `ijson`, and write a first draft of the Python code. I then spent approximately 2 hours gaining a deeper understanding of the schema and the domain to solve the problem, experimenting with various strategies. Finally, I spent another hour writing this README and performing additional cross-referencing with the search tool.

In total, this took over 4 hours.

### Compute

On my system, the script takes approximately 1.5 minutes to run.

```
$ time python3 extract_urls.py 2024-07-01_anthem_index.json
...
real    1m32.585s
user    1m14.186s
sys     0m6.448s
```

My system is a MacBook Pro with a Quad-Core Intel Core i7 (2.7 GHz) and 16 GB of memory.
