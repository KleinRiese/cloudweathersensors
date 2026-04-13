# Cloud Weather Sensors

HACS Custom Integration for Netatmo Weather Stations. This is NOT an official Netatmo integration.

## Features
- Config Flow with client_id, client_secret, refresh_token

- Reauth support for authentication errors

- Sensors for available station and module values

- Diagnostics with redaction of sensitive data

- Local brand files for Home Assistant 2026.3+

## Configuration
- Create App: https://dev.netatmo.com/apps/
- Enter details. App Name can be freely chosen.
- Create token, scope "read_station"

Then configure the integration with these values:
Required:

- client_id
- client_secret
- refresh_token

These values come from your Netatmo App at dev.netatmo.com.

## Note
Which weather stations appear is determined by Netatmo via the API's favorites response.
The stations to query are set at 'https://weathermap.netatmo.com/' (simply save one or more as favorites).