from datetime import date, timedelta
import os

import requests


def get_cookies():
  COOKIE_ENV_VARS = {
  "ASP.NET_SessionId": "SCCJSP_SESSION",
  "FedAuth": "SCCJSP_FEDAUTH",
  "FedAuth1": "SCCJSP_FEDAUTH1",
  }
  return {
    k: os.environ[v]
    for k, v in COOKIE_ENV_VARS.items()
  }

def get_data():
  session = requests.session()
  session.cookies.update(get_cookies())

  tomorrow_formatted = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
  session.post("https://cjs.shelbycountytn.gov/CJS/Hearing/SearchHearings/HearingSearch",
    data = {
      "PortletName": "HearingSearch",
      "Settings.CaptchaEnabled": "False",
      "Settings.DefaultLocation": "All Locations",
      "SearchCriteria.SelectedCourt": "All Locations",
      "SearchCriteria.SelectedHearingType": "All Hearing Types",
      "SearchCriteria.SearchByType": "Courtroom",
      "SearchCriteria.SelectedCourtRoom": "1088",
      "SearchCriteria.DateFrom": tomorrow_formatted,
      "SearchCriteria.DateTo": tomorrow_formatted,
    })
  
  resp = session.post("https://cjs.shelbycountytn.gov/CJS/Hearing/HearingResults/Read",
    data = {
      "sort": "",
      "group": "", 
      "filter": "",
      "portletId": "27",
    })

  return resp.json()

def print_data(data):
  for hearing in data["Data"]:
    print(f'hearing for {hearing["DefendantName"]} at {hearing["HearingTime"]} on {hearing["HearingDate"]} with {hearing["JudgeParsed"]} presiding.')


def main():
  data = get_data()
  print_data(data)

if __name__ == "__main__":
  main()
