# fetchers.py querys data

import urllib3
import json
from os import environ

def get_nautobot_devices(node):
  """ Returns nautobot_devices """
  try:
    http = urllib3.PoolManager()
    nautobot_token = environ.get('NAUTOBOT_TOKEN', None)
    nautobot_url = environ.get('NAUTOBOT_URL', "https://nautobot.eencloud.com/api")
    # nautobot_token = "4a623f14427953a4e87d7cc2a7cdde1ba8b406ec"
    # nautobot_url = "https://nautobot.eencloud.com/api"
    nautobot_headers =  {
      "Accept": "application/json; version=2.0; indent=4",
      "Authorization": f"Token {nautobot_token}",
      "Content-Type": "application/json"
  }
    query_results = http.request(
          "GET",
          f"{nautobot_url}/dcim/devices/?q={node}",
          headers=nautobot_headers,
          redirect=True)

    print(query_results.data)

    data = json.loads(query_results.data.decode('utf-8'))

    nautobot_devices = []

    if data.get('count', 0) > 0:
      for k, device in enumerate(data['results']):
        device = data['results'][k]

        # Handle optional fields that might be None
        rack_info = "N/A"
        if device.get('rack') and device['rack'] is not None:
          device['url'] = device['url'].replace("/api/", "/", 1)
          rack_id = device['rack'].get('id', 'N/A')
          rack_display = device['rack'].get('display', 'N/A')
          rack_url = device['rack'].get('url', '').replace("/api/", "/", 1)
          rack_info = f"[Rack: {rack_display} - {rack_id}]({rack_url})" if rack_url else str(rack_id)

        k8s_version = "N/A"
        if device.get('custom_fields') and device['custom_fields'] is not None:
          k8s_version = device['custom_fields'].get('kubernetes_version') or 'N/A'

        nautobot_devices.append(f"""
Device name: [{device.get('name', 'Unknown')}]({device.get('url', '')})
{rack_info}
Kubernetes version: {k8s_version}
""")
    return nautobot_devices

  except OSError as err:
    print(f"OSError: {err}")
    return []
  except AttributeError as err:
    print(f"AttributeError: {err}")
    return []
  except json.JSONDecodeError as err:
    print(f"JSON decode error: {err}")
    return []
  except Exception as err:
    print(f"Unexpected error: {err}")
    return []
