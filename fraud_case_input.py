import csv
import json


def dedupe_per_case(case_filename: str) -> list[dict[str, str]]:
    deduped_cases = {}

    with open(case_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        # Iterate through each row and keep the one with the lowest chain, contract_address, token_id sorting
        for row in reader:
            case_id = row['case_id']
            chain = row['chain']
            contract_address = row['contract_address']
            token_id = row['token_id']

            # Create a tuple for comparison (chain, contract_address, token_id)
            sort_key = (chain, contract_address, token_id)

            # Only keep the row with the smallest tuple for each case_id
            if case_id not in deduped_cases or sort_key < deduped_cases[case_id]['sort_key']:
                deduped_cases[case_id] = {key: row[key] for key in
                                          ["organization_name", "chain", "contract_address", "token_id", "token_status",
                                           "case_id", "report_status"]}
                deduped_cases[case_id]['sort_key'] = sort_key  # Store the sort key to compare in future rows

    # Convert deduped_cases dictionary back into a list without the sort_key
    result = [{k: v for k, v in case.items() if k != 'sort_key'} for case in deduped_cases.values()]

    return result


def associate_token_images(token_cases: list[dict[str, str]], token_filename: str):
    # Load the token data into a dictionary for easy lookup
    token_data = {}

    with open(token_filename, mode='r', encoding='utf-8') as file:
        csv.field_size_limit(10000000)
        reader = csv.DictReader(file)

        for row in reader:
            chain = row['contract_chain']
            contract_address = row['contract_address']
            token_id = row['token_id']
            data = row['data']

            # Parse the JSON string in the "data" column to extract the preview_url
            preview_url = None  # Default to None if JSON parsing fails or key is missing
            if data:
                try:
                    parsed_data = json.loads(data)
                    if isinstance(parsed_data, dict):
                        media = parsed_data.get("media", None)
                        if media is not None:
                            preview_url = media.get("preview_url", None)
                except json.JSONDecodeError:
                    pass  # Ignore parsing errors and continue

            # Only store entries with a valid preview_url
            if preview_url:
                token_data[(chain, contract_address, token_id)] = preview_url

    # Filter deduplicated cases to retain only rows with a matching preview_url
    result = []
    for case in token_cases:
        key = (case['chain'], case['contract_address'], case['token_id'])
        if key in token_data:  # Ensure only inner join (where preview_url is present)
            case['preview_url'] = token_data[key]  # Add preview_url
            result.append(case)

    return result


def load_fraud_case_images(case_filename: str, token_filename: str):
    deduped_tokens = dedupe_per_case(case_filename)
    tokens = associate_token_images(deduped_tokens, token_filename)
    return tokens


if __name__ == '__main__':
    load_fraud_case_images("fraud_case_images.csv", "token_data.csv")