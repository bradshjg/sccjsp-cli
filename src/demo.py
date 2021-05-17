import csv
from datetime import date, timedelta
from getpass import getpass
import os

from bs4 import BeautifulSoup
import requests

LOGIN_AUTH_TOKEN_NAME = '__RequestVerificationToken'
LOGIN_GET_URL = 'https://cjs.shelbycountytn.gov/CJS/Account/Login'
LOGIN_POST_URL = 'https://cjs.shelbycountytn.gov/CJS/'


class LoginFailed(Exception):
  pass


def login(session):
  username = os.environ.get('SCCJSP_USERNAME') or input('username: ')
  password = os.environ.get('SCCJSP_PASSWORD') or getpass('password: ')
  login_get_resp = session.get(LOGIN_GET_URL)
  login_get_parsed = BeautifulSoup(login_get_resp.content, 'html.parser')
  token = login_get_parsed.find('input', {'name': LOGIN_AUTH_TOKEN_NAME})
  login_data = {
    LOGIN_AUTH_TOKEN_NAME: token.get('value'),
    'UserName': username,
    'Password': password
  }
  login_post_resp = session.post(login_get_resp.url, data=login_data)
  login_post_parsed = BeautifulSoup(login_post_resp.content, 'html.parser')
  sso_data = {
    hidden_input.get('name'): hidden_input.get('value')
    for hidden_input in login_post_parsed.find_all('input', {'type': 'hidden'})
  }
  action = login_post_parsed.find('form').get('action')
  if action != LOGIN_POST_URL:
    raise LoginFailed
  session.post(action, data=sso_data)

def get_data():
  session = requests.session()
  login(session)

  tomorrow_formatted = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
  session.post("https://cjs.shelbycountytn.gov/CJS/Hearing/SearchHearings/HearingSearch",
    data = {
      "PortletName": "HearingSearch",
      "Settings.CaptchaEnabled": "False",
      "Settings.DefaultLocation": "All Locations",
      "SearchCriteria.SelectedCourt": "All Locations",
      "SearchCriteria.SelectedHearingType": "All Hearing Types",
      "SearchCriteria.SearchByType": "Courtroom",
      "SearchCriteria.SelectedCourtRoom": "1088",  # Division 10
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

def write_data(data):
  to_write = data['Data']
  with open('data.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=to_write[0].keys())
    writer.writeheader()
    writer.writerows(to_write)


def main():
  data = get_data()
  write_data(data)

if __name__ == "__main__":
  main()
