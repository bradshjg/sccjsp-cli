import csv
from datetime import date, timedelta
from io import StringIO
from urllib.parse import parse_qs

from bs4 import BeautifulSoup
from chalice import Chalice, Response
import requests

app = Chalice(app_name='demo-app')

LOGIN_AUTH_TOKEN_NAME = '__RequestVerificationToken'
LOGIN_GET_URL = 'https://cjs.shelbycountytn.gov/CJS/Account/Login'
LOGIN_POST_URL = 'https://cjs.shelbycountytn.gov/CJS/'
SEARCH_URL = 'https://cjs.shelbycountytn.gov/CJS/Hearing/SearchHearings/HearingSearch'
SEARCH_READ_URL = 'https://cjs.shelbycountytn.gov/CJS/Hearing/HearingResults/Read'


class LoginFailed(Exception):
  pass


def get_data(username, password):
  session = requests.session()
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

  tomorrow_formatted = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
  session.post(SEARCH_URL,
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
  
  resp = session.post(SEARCH_READ_URL,
    data = {
      "sort": "",
      "group": "", 
      "filter": "",
      "portletId": "27",
    })

  data = resp.json()['Data']
  csvfile = StringIO()
  writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
  writer.writeheader()
  writer.writerows(data)
  return csvfile.getvalue()


HTML = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>SCCJSP</title>
  </head>
  <body>
    <h1>Get the Data!</h1>
    <form action="download" method="post">
      <label>Username:
        <input name="username">
      </label>
      <label>Password:
        <input type="password" name="password">
      </label>
      <input type="submit" value="Download Data">
    </form>
  </body>
</html>
'''


@app.route('/')
def index():
    return Response(body=HTML,
                    status_code=200,
                    headers={'Content-Type': 'text/html'})

@app.route('/download', methods=['POST'], content_types=['application/x-www-form-urlencoded'])
def download():
    request = app.current_request
    parsed = parse_qs(request.raw_body.decode())
    try:
        data = get_data(parsed['username'][0], parsed['password'][0])
    except LoginFailed:
        data = 'Login failed'
    return Response(body=data,
                    status_code=200,
                    headers={
                        'Content-Type': 'text/csv',
                        'Content-Disposition': 'attachment; filename="data.csv"'
                    })
