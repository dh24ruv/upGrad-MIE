import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/Users/dhruvpande/upgrad/.env")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_company(name: str) -> dict | None:
    """
    Try to find a company in the database.
    Returns the company dict if found, None if not.
    """
    result = supabase.table("companies") \
        .select("*") \
        .ilike("name", f"%{name}%") \
        .limit(1) \
        .execute()

    if result.data:
        return result.data[0]
    return None

def get_all_companies() -> list:
    result = supabase.table("companies") \
        .select("*") \
        .execute()
    return result.data

if __name__ == "__main__":
    companies = get_all_companies()
    print(f"Total companies in database: {len(companies)}")
    
    name = input("Search for a company: ")
    result = get_company(name)
    
    if result:
        print("\nFound:")
        for k, v in result.items():
            if v is not None:
                print(f"  {k}: {v}")
    else:
        print("\nNot found in database.")