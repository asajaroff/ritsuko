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

    # Check for HTTP errors (404, 403, etc.)
    if query_results.status == 404:
      print(f"Device '{node}' not found in Nautobot")
      return [f"**Error**: Device `{node}` not found in Nautobot.\n\nPlease verify the device name is correct."]
    elif query_results.status == 403:
      print(f"Access forbidden to Nautobot for device '{node}'")
      return [f"**Error**: Access forbidden when querying device `{node}`. The Nautobot token may be invalid or lack necessary permissions."]
    elif query_results.status >= 400:
      print(f"HTTP error {query_results.status} when querying device '{node}'")
      return [f"**Error**: Failed to retrieve device `{node}` from Nautobot (HTTP {query_results.status})."]

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

          try:
            rack_query = http.request(
                  "GET",
                  f"{nautobot_url}/dcim/racks/{rack_id}",
                  headers=nautobot_headers,
                  redirect=True)

            # Check for HTTP errors on rack query
            if rack_query.status >= 400:
              print(f"Failed to retrieve rack {rack_id} (HTTP {rack_query.status})")
              rack_info = f"Rack:\t{rack_id} (details unavailable)"
            else:
              # https://nautobot.eencloud.com/api/dcim/racks/a283344f-a59c-466d-8fb5-cd1055aeac80/
              data_rack = json.loads(rack_query.data.decode('utf-8'))

              # rack_display = device['rack'].get('name', 'N/A')
              rack_url = device['rack'].get('url', '').replace("/api/", "/", 1)
              rack_name = data_rack.get('name', str(rack_id))
              rack_info = f"Rack:\t[{rack_name}]({rack_url})" if rack_url else str(rack_id)
          except json.JSONDecodeError as e:
            print(f"Failed to parse rack data for {rack_id}: {e}")
            rack_info = f"Rack:\t{rack_id} (parse error)"
          except Exception as e:
            print(f"Unexpected error querying rack {rack_id}: {e}")
            rack_info = f"Rack:\t{rack_id} (query failed)"

        k8s_version = "N/A"
        if device.get('custom_fields') and device['custom_fields'] is not None:
          k8s_version = device['custom_fields'].get('kubernetes_version') or 'N/A'

        nautobot_devices.append(f"""
Device name: [{device.get('name', 'Unknown')}]({device.get('url', '')})
{rack_info}
Position: {device.get('position', 'N/A')}
Kubernetes version: {k8s_version}
""")
    return nautobot_devices

  except OSError as err:
    print(f"OSError: {err}")
    return [f"**Error**: Network error when connecting to Nautobot: {str(err)}"]
  except AttributeError as err:
    print(f"AttributeError: {err}")
    return [f"**Error**: Failed to process Nautobot response data: {str(err)}"]
  except json.JSONDecodeError as err:
    print(f"JSON decode error: {err}")
    return [f"**Error**: Failed to parse Nautobot data for device `{node}`. The data may be corrupted or in an unexpected format."]
  except Exception as err:
    print(f"Unexpected error: {err}")
    return [f"**Error**: An unexpected error occurred while retrieving device `{node}`: {str(err)}"]
