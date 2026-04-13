
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTRIBUTION


@dataclass(frozen=True, kw_only=True)
class NetatmoMetricDescription(SensorEntityDescription):
    source_key: str


STATION_METRICS = (
    NetatmoMetricDescription(key="pressure", source_key="Pressure", name="Pressure", native_unit_of_measurement=UnitOfPressure.HPA, device_class=SensorDeviceClass.PRESSURE, state_class=SensorStateClass.MEASUREMENT),
    NetatmoMetricDescription(key="absolute_pressure", source_key="AbsolutePressure", name="Absolute pressure", native_unit_of_measurement=UnitOfPressure.HPA, device_class=SensorDeviceClass.PRESSURE, state_class=SensorStateClass.MEASUREMENT),
)

MODULE_METRICS = (
    NetatmoMetricDescription(key="temperature", source_key="Temperature", name="Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    NetatmoMetricDescription(key="humidity", source_key="Humidity", name="Humidity", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT),
    NetatmoMetricDescription(key="wind_strength", source_key="WindStrength", name="Wind strength", native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-windy"),
    NetatmoMetricDescription(key="wind_angle", source_key="WindAngle", name="Wind angle", native_unit_of_measurement="°", icon="mdi:compass"),
    NetatmoMetricDescription(key="gust_strength", source_key="GustStrength", name="Gust strength", native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-windy-variant"),
    NetatmoMetricDescription(key="gust_angle", source_key="GustAngle", name="Gust angle", native_unit_of_measurement="°", icon="mdi:compass-rose"),
    NetatmoMetricDescription(key="rain", source_key="Rain", name="Rain", native_unit_of_measurement=UnitOfLength.MILLIMETERS, state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-rainy"),
    NetatmoMetricDescription(key="rain_1h", source_key="sum_rain_1", name="Rain 1h", native_unit_of_measurement=UnitOfLength.MILLIMETERS, state_class=SensorStateClass.TOTAL, icon="mdi:weather-pouring"),
    NetatmoMetricDescription(key="rain_24h", source_key="sum_rain_24", name="Rain 24h", native_unit_of_measurement=UnitOfLength.MILLIMETERS, state_class=SensorStateClass.TOTAL, icon="mdi:weather-pouring"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    stations = coordinator.data.get("stations", {})
    for station_id, station in stations.items():
        dash = station.get("dashboard_data") or {}
        station_name = station.get("station_name") or station_id
        for description in STATION_METRICS:
            if description.source_key in dash:
                entities.append(NetatmoMetricSensor(coordinator, entry.entry_id, "station", station_id, station_name, description))

        for mod in station.get("modules") or []:
            mod_id = mod.get("_id")
            if not mod_id:
                continue
            mod_name = mod.get("module_name") or mod.get("type") or mod_id
            parent_name = f"{station_name} / {mod_name}"
            mdash = mod.get("dashboard_data") or {}
            for description in MODULE_METRICS:
                if description.source_key in mdash:
                    entities.append(NetatmoMetricSensor(coordinator, entry.entry_id, "module", mod_id, parent_name, description))

    async_add_entities(entities)


class NetatmoMetricSensor(CoordinatorEntity, SensorEntity):
    entity_description: NetatmoMetricDescription
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, scope: str, parent_id: str, parent_name: str, description: NetatmoMetricDescription) -> None:
        super().__init__(coordinator)
        self._scope = scope
        self._parent_id = parent_id
        self._parent_name = parent_name
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{scope}_{parent_id}_{description.key}".lower()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._parent_id)},
            name=self._parent_name,
            manufacturer="Netatmo",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if self._scope == "station":
            parent = data.get("stations", {}).get(self._parent_id) or {}
        else:
            parent = data.get("modules", {}).get(self._parent_id) or {}
        return (parent.get("dashboard_data") or {}).get(self.entity_description.source_key)

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        if self._scope == "station":
            parent = data.get("stations", {}).get(self._parent_id) or {}
        else:
            parent = data.get("modules", {}).get(self._parent_id) or {}
        return bool(parent.get("reachable", True))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {
            "source": "cloud_weather_sensors_api",
            "scope": self._scope,
            "parent_id": self._parent_id,
        }
