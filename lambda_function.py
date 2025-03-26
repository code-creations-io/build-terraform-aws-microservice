import os
import requests
import traceback
import time
import math
import json

def organization_handler(body):
    company_name = body.get("company_name")
    if not company_name:
        return {"error": "no company name provided"}, 400

    countries = body.get("countries", [])
    countries_param_string = "&".join([f"organization_locations[]={country}" for country in countries])
    
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": os.environ.get("APOLLO_API_KEY")
    }
    results = []
    page = 1
    page_size = 100
    base_url = f"https://api.apollo.io/api/v1/mixed_companies/search?per_page={page_size}&q_organization_name={company_name}&{countries_param_string}"

    try:
        # Make first call
        response = requests.post(f"{base_url}&page={page}", headers=headers)
        if response.status_code == 429:
            print(f"\nERROR ({response.status_code}):\n{response.content}\n")
            return {"error": "rate limit exceeded"}, 429
        if response.status_code != 200:
            print(f"\nERROR ({response.status_code}):\n{response.content}\n")
            return {"error": "internal server error"}, 500

        data = response.json()
        pagination = data.get("pagination", {})
        current_page = pagination.get("page")
        total_pages = pagination.get("total_pages")
        results += data.get("organizations", [])

        # If only one page, return the results
        if current_page >= total_pages:
            results = [res["id"] for res in results]
            return results, 200

        # Make subsequent calls
        for page in range(2, total_pages + 1):
            time.sleep(2)
            try:
                url = f"{base_url}&page={page}"
                print(f"Requesting: {url}")
                response = requests.post(url, headers=headers)
                if response.status_code == 429:
                    print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                    return {"error": "rate limit exceeded"}, 429
                if response.status_code != 200:
                    print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                    continue

                data = response.json()
                print(f"\tPage {page}/{total_pages}")
                results += data.get("organizations", [])
            except Exception:
                print(f"ERROR: {traceback.format_exc()}")

        results = [res["id"] for res in results]
        return results, 200
    except Exception:
        print(traceback.format_exc())
        return {"error": "exception occurred"}, 500

def people_handler(body):
    limit = body.get("limit", 3)
    org_ids = body.get("organization_ids", [])
    if not org_ids:
        return {"error": "no organization_ids provided"}, 400

    job_titles = body.get("job_titles", [])
    if not job_titles:
        return {"error": "no job_titles provided"}, 400

    person_locations = body.get("person_locations", [])
    org_locations = body.get("organization_locations", [])
    contact_email_status = "verified"

    job_title_param_string = "&".join([f"person_titles[]={job_title}" for job_title in job_titles])
    org_locations_param_string = "&".join([f"organization_locations[]={location}" for location in org_locations])
    person_locations_param_string = "&".join([f"person_locations[]={location}" for location in person_locations])
    org_param_string = "&".join([f"organization_ids[]={org}" for org in org_ids])

    print(f"Number of organisation IDs: {len(org_ids)}")
    max_num_orgs_batch = 100
    rounds = math.ceil(len(org_ids) / max_num_orgs_batch)
    print(f"Number of rounds: {rounds}")
    results = []

    for round in range(0, rounds):
        print(f"Round: {round}")
        org_ids_chunk = org_ids[round * max_num_orgs_batch:(round + 1) * max_num_orgs_batch]
        org_param_string = "&".join([f"organization_ids[]={org}" for org in org_ids_chunk])

        try:
            headers = {
                "accept": "application/json",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "x-api-key": os.environ.get("APOLLO_API_KEY")
            }
            page = 1
            page_size = limit
            base_url = (
                f"https://api.apollo.io/api/v1/mixed_people/search?per_page={page_size}&"
                f"{job_title_param_string}&{org_param_string}&{org_locations_param_string}&"
                f"{person_locations_param_string}&contact_email_status[]={contact_email_status}"
            )
            print("Requesting: ", base_url)

            response = requests.post(f"{base_url}&page={page}", headers=headers)
            if response.status_code == 429:
                print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                return {"error": "rate limit exceeded"}, 429
            if response.status_code != 200:
                print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                return {"error": "internal server error"}, 500

            data = response.json()
            pagination = data.get("pagination", {})
            current_page = pagination.get("page")
            total_pages = pagination.get("total_pages")
            results += data.get("people", [])

            if current_page >= total_pages:
                continue

            for page in range(2, total_pages + 1):
                if len(results) >= limit:
                    break
                time.sleep(2)
                try:
                    url = f"{base_url}&page={page}"
                    print(f"Requesting: {url}")
                    response = requests.post(url, headers=headers)
                    if response.status_code == 429:
                        print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                        return {"error": "rate limit exceeded"}, 429
                    if response.status_code != 200:
                        print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                        continue

                    data = response.json()
                    print(f"\tPage {page}/{total_pages}")
                    results += data.get("people", [])
                except Exception:
                    print(f"ERROR: {traceback.format_exc()}")

        except Exception:
            print(traceback.format_exc())
            return {"error": "exception occurred"}, 500
    
    response_data = [res["id"] for res in results]
    return response_data, 200

def enrichment_handler(body):
    people_ids = body.get("people_ids", [])
    if not people_ids:
        return {"error": "no people_ids provided"}, 400

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": os.environ.get("APOLLO_API_KEY")
    }
    results = []
    page = 1
    base_url = "https://api.apollo.io/api/v1/people/bulk_match?reveal_personal_emails=true"
    print("Requesting: ", base_url)
    rounds = math.ceil(len(people_ids) / 10)
    print(f"Number of rounds: {rounds}")

    try:
        for r in range(0, rounds):
            print(f"Round: {r}")
            try:
                chunk = people_ids[r * 10:(r + 1) * 10]
                payload = {
                    "details": [{"id": person_id} for person_id in chunk]
                }
                response = requests.post(f"{base_url}&page={page}", headers=headers, json=payload)
                if response.status_code == 429:
                    print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                    return {"error": "rate limit exceeded"}, 429
                if response.status_code != 200:
                    print(f"\nERROR ({response.status_code}):\n{response.content}\n")
                    continue

                data = response.json()
                if data.get("status") != "success":
                    continue

                results.extend(data.get("matches", []))
            except Exception:
                print(f"ERROR: {traceback.format_exc()}")

        formatted_results = [
            {
                "id": res["id"],
                "first_name": res.get("first_name", ""),
                "last_name": res.get("last_name", ""),
                "linkedin_url": res.get("linkedin_url", ""),
                "twitter_url": res.get("twitter_url", ""),
                "title": res.get("title", ""),
                "email": res.get("email", ""),
                "state": res.get("state", ""),
                "city": res.get("city", ""),
                "country": res.get("country", ""),
                "organization": res.get("organization", {}).get("name", ""),
                "phone": res.get("organization", {}).get("phone", ""),
            }
            for res in results
        ]
        return formatted_results, 200
    except Exception:
        print(traceback.format_exc())
        return {"error": "exception occurred"}, 500

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Invalid JSON in request body"})
        }

    endpoint = body.get("endpoint")
    if not endpoint:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "No endpoint provided in request body"})
        }

    # Route to the appropriate handler based on the "endpoint" field
    if endpoint == "organization":
        result, status = organization_handler(body)
    elif endpoint == "people":
        result, status = people_handler(body)
    elif endpoint == "enrichment":
        result, status = enrichment_handler(body)
    else:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Unknown endpoint: {endpoint}"})
        }

    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
