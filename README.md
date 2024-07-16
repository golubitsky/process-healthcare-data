## Overview

This repo contains a solution to https://github.com/serif-health/takehome. Please refer to the README.md in that repo for the purpose of this repo.

## Solution

Cross-referencing the 50 URLs containing "NY" with information from the search tool (manually), we get **14 URLs**, listed in `urls_corresponding_to_anthems_ppo_in_new_york_state.txt`.

I have also saved the `intermediate_output_from_script.txt`, annotated at the end of each row with the cross-references using the search tool.

For more information, see the sections "Explanation and Strategy" and "Performance" below.

## Install

1. Tested with Python 3.12.3; download it from [here](https://www.python.org/downloads).
2. From project root, install dependencies using `pip3 install -r requirements.txt`.

## Run

```sh
python3 extract_urls.py 2024-07-01_anthem_index.json
```

## Difficulty in identifying a consistent MRF-naming convention

Unfortunately, "The individual in-network rate files linked to the Table of Contents file need not follow a defined naming convention" [source](https://www.cms.gov/healthplan-price-transparency/resources/technical-clarification).

I also found a discussion mentioning the inconsistent and/or unspecified file naming conventions, in particular about Anthem:
https://github.com/CMSgov/price-transparency-guide/discussions/619.

## Explanation and Strategy

We have 3 sources of information:

1.  In each `reporting_structure` element, a list of plans that have pricing data across multiple MRFs; most plans are identified with an EIN.
2.  In each `reporting_structure` element, a List of MRFs corresponding to the list of plans in the same `reporting_structure` element.
3.  Separately, a UI search tool provided by Anthem: https://www.anthem.com/machine-readable-file/search/; we can search by EIN.

### First approach: identify relevant plans first

Here's how I first chose to approach the problem:

```
for each reporting_structure:
  if any of `reporting_plans` can be identified as PPO and New York:
    examine the corresponding `in_network_files`
```

The second line proved difficult without structured data to identify the plan as such. I tried searching for a combination of `reporting_plan['plan_name']` matching these conditions (converted to lowercase):

- contains "ny" or "new york"
- contains "ppo"

But the downside here is that not all plans definitely have names according to these rules. I discovered this upon examining the `in_network_files`.

Not only that, but having found such plans, the problem remained — how to identify the correct URLs?

### Using the hint about Anthem vs Highmark

I inspected the `description` of the `in_network_files`. While many descriptions referenced (converted to lowercase) 'new york' and 'ppo', such descriptions invariably also referenced 'highmark'. Anthem is NOT the same as Highmark. Per https://www.bcbs.com/bcbs-companies-and-licensees, there are four BCBS companies operating in New York:

- Anthem Blue Cross Blue Shield
- Highmark Blue Cross Blue Shield of Western New York
- Highmark Blue Shield of Northeastern New York
- Excellus BlueCross BlueShield

Of these four, we are interested only in Anthem.

Thus, though there are many URLs for files with descriptions happily containing both 'new york' and 'ppo', such URLs are ruled out because they clearly apply to Highmark and NOT to Anthem.

The first approach lead to a dead end.

### Second approach: identify relevant URLs first

I decided to flip the algorithm:

```
for each reporting_structure:
  if any of the `in_network_files` URLs contain 'NY'
    examine the corresponding `reporting_plans` for evidence that _any one of them_ is a PPO
```

It turned out that each of the matching `in_network_files` had a consist description of "In-Network Negotiated Rates Files", which seemed promising.

There turned out to be 50 such URLs pointing to file names like ``.

### Hypothesis on Anthem's MRF naming convention

These 50 URLs follow a convention summarized by two representative example file names:

1. NY_PPPNMED0001.json.gz
2. NY_GGHAMEDAP33_08_09.json.gz

Based on these two representative example file names, the convention could be:

1. 2 chars: State Abbreviation: NY stands for New York.
2. <underscore>
3. 4 chars: Plan/Region Code (?)
   1. examples of PPOs include GGHA, HXPX, HYRE
   2. examples of non-PPOs include JBDT
4. 3 chars: Service Type: value is always MED; probably stands for Medical (?)
5. 4 chars: Sequence Number or Identifier (?); examples include 0001 or AP33
6. <underscore>
7. 2 chars (only for MRFs split into multiple files): index of this MRF
8. <underscore>
9. 2 chars (only for MRFs split into multiple files): number of files into which the MRF is split

### Second approach continued: heuristic to identify PPOs

At this point, without knowing Anthem's naming convention, there is not enough information to identify each of these URLs as pointing to a PPO or not. But again, using the hint about the tool https://www.anthem.com/machine-readable-file/search/, we can glean information from the UI that is not present in the table of contents file.

To use the UI, we need EINs, which come from each plan. Given the 50 URLs containing "NY" (see above), I decided to:

```
for each reporting_structure:
  if any of the `in_network_files` URLs contain 'NY'
    examine the corresponding `reporting_plans` for evidence that _any one of them_ is a PPO
```

To complete the final step, we can search for 'ppo' in the name of any plan.

The UI in this tool makes the distinction between PPO and EPO (and FFS, POS); the file names themselves do NOT make the distinction.

- PPO
  - Example EIN: 37-1441668
  - Example file name: NY_GGHAMEDAP33_01_09.json.gz
- EPO
  - Example EIN: 37-1441668
  - Example file name: NY_GZHYMEDAP36.json.gz
- Highmark
  - identified using `description` field contains "highmark"
  - Example EIN: 85-4347090
  - Example file name: 2024-07_800_72A0_in-network-rates_01_of_02.json.gz
    - File name doesn't contain "NY\_" so we won't have false positives.

One problem is that Anthem's naming convention for MRFs seems to not differentiate between EPOs and PPOs.

Edge cases:

- For EIN 38-4042589 there is a file that appears as both PPO and EPO
  - https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/NY_GZHYMEDAP36.json.gz
- NY_JBDTMED0000.json.gz no ppo found; example EIN that references this file 87-2928230 K HEALTH - WCM SERVICES LLC - ANTHEM
  - but this file _is_ for a PPO, according to the tool
- Similarly, for EIN 87-2928230 the tool shows that NY*HXNWMED0000.json.gz \_is* for a _PPO_, but it was ruled out using the method I used
- For EIN 13-3680053, it references both NY_HXPYMED0004.json.gz (EPO according to the tool) and NY_HXPXMED0009.json.gz (PPO according to the tool)
  - this uncovers another edge case where NY_HXPYMED0004.json.gz has to be ruled out manually using the tool

## Performance

### Human

It took me an hour or so to figure out how to load the large file, how to use the Python library `ijson`, and to write a "first draft" of the Python code. From there, I spent about 2 hours getting my head around the schema and trying to understand the domain enough to solve the problem, trying the various strategies above. I took another 1 hour to write this README and do additional cross-referencing with the search tool.

Over 4 hours total.

### Compute

On my system, the script takes ~1.5 minutes to run.

```
$ time python3 extract_urls.py 2024-07-01_anthem_index.json
...
real    1m32.585s
user    1m14.186s
sys     0m6.448s
```

My system is a MacBook Pro with a Quad-Core Intel Core i7 (2.7 GHz), with 16 GB of memory.
