import gspread
from google.oauth2.service_account import Credentials

def get_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(
        # "https://docs.google.com/spreadsheets/d/17LHgbae8K0OxZlXUHulOtZnDn66Oapy5z9bClJDjtEA/edit#gid=0"
        "https://docs.google.com/spreadsheets/d/1-wJUCSyZQZ_dKsZA7TUhncb_A3Ln84slLfTvDkAR4VQ"
    )

    sheet_summary = spreadsheet.worksheet("Summary")
    sheet_per2jam = spreadsheet.worksheet("Per 2 Jam")

    return {
        "Summary": sheet_summary,
        "Per 2 Jam": sheet_per2jam
    }