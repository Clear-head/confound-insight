import requests

class MFDSClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService05/getDrugPrdtPrmsnInq05"

    def fetch_products(self, item_name, page_no=1, num_of_rows=10):
        params = {
            'serviceKey': self.api_key,
            'item_name': item_name,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'type': 'json'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()