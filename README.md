# Cloud Weather Sensors

The **Cloud Weather Sensors** integration allows you to use data from nearby Netatmo weather stations in Home Assistant.

> This is **not** an official Netatmo integration.

---

## Supported features

* Retrieve data from one or more nearby weather stations
* Create multiple sensor entities per station
* Automatic grouping of sensors

---

## Prerequisites

Before setting up the integration, you need to create Netatmo API credentials.

### Create API credentials

1. Go to https://dev.netatmo.com/apps/
2. Log in and open **My Apps**
3. Create a new app
4. Fill in the required details

<img width="1392" height="635" alt="image" src="https://github.com/user-attachments/assets/ce45c0e2-d115-4c43-8823-383831951bfd" />

5. Generate an access token:

   * Select the scope `read_station`
   * Click **Generate Token**

<img width="1124" height="230" alt="image" src="https://github.com/user-attachments/assets/2bcaf3aa-1b40-4f5c-ac06-873f56edb65e" />

6. Note the following values:

   * `client_id`
   * `access_token`
   * `refresh_token`

---

### Select weather stations

1. Go to https://weathermap.netatmo.com/
2. Browse the map
3. Identify stations near your location

---

## Installation

### HACS

1. Open HACS in Home Assistant

2. Add this repository as a custom repository:

   ```
   https://github.com/KleinRiese/cloudweathersensors
   ```

3. Select **Integration** as the category

4. Install the integration

5. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Cloud Weather Sensors**
4. Enter your credentials:

   * `client_id`
   * `access_token`
   * `refresh_token`

---

## Entities

The integration creates sensor entities based on the selected weather stations.

* Up to 4 groups per station are created
* Each group contains multiple sensor entities
* Entity names are generated automatically

---

## Notes

* Data quality depends on the selected weather stations
* Using multiple stations may improve accuracy
* Netatmo API rate limits may apply

---

## Troubleshooting

If you encounter issues:

* Verify that your API credentials are correct
* Ensure the token has the `read_station` scope
* Check Home Assistant logs for error messages

---

## Disclaimer

This project is not affiliated with or endorsed by Netatmo.
