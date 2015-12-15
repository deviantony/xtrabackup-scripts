import requests


class HttpManager:

    def post(self, url, json):
        requests.post(url, json=json)
