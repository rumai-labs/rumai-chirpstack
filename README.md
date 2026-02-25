# ChirpStack Docker example

This repository contains a skeleton to setup the [ChirpStack](https://www.chirpstack.io)
open-source LoRaWAN Network Server (v4) using [Docker Compose](https://docs.docker.com/compose/).

**Note:** Please use this `docker-compose.yml` file as a starting point for testing
but keep in mind that for production usage it might need modifications. 

## Directory layout

* `docker-compose.yml`: the docker-compose file containing the services
* `configuration/chirpstack`: directory containing the ChirpStack configuration files
* `configuration/chirpstack-gateway-bridge`: directory containing the ChirpStack Gateway Bridge configuration
* `configuration/mosquitto`: directory containing the Mosquitto (MQTT broker) configuration
* `configuration/postgresql/initdb/`: directory containing PostgreSQL initialization scripts

## Configuration

This setup is pre-configured for all regions. You can either connect a ChirpStack Gateway Bridge
instance (v3.14.0+) to the MQTT broker (port 1883) or connect a Semtech UDP Packet Forwarder.
Please note that:

* You must prefix the MQTT topic with the region.
  Please see the region configuration files in the `configuration/chirpstack` for a list
  of topic prefixes (e.g. eu868, us915_0, au915_0, as923_2, ...).
* The protobuf marshaler is configured.

This setup also comes with two instances of the ChirpStack Gateway Bridge. One
is configured to handle the Semtech UDP Packet Forwarder data (port 1700), the
other is configured to handle the Basics Station protocol (port 3001). Both
instances are by default configured for EU868 (using the `eu868` MQTT topic
prefix).

### Reconfigure regions

ChirpStack has at least one configuration of each region enabled. You will find
the list of `enabled_regions` in `configuration/chirpstack/chirpstack.toml`.
Each entry in `enabled_regions` refers to the `id` that can be found in the
`region_XXX.toml` file. This `region_XXX.toml` also contains a `topic_prefix`
configuration which you need to configure the ChirpStack Gateway Bridge
UDP instance (see below).

#### ChirpStack Gateway Bridge (UDP)

Within the `docker-compose.yml` file, you must replace the `eu868` prefix in the
`INTEGRATION__..._TOPIC_TEMPLATE` configuration with the MQTT `topic_prefix` of
the region you would like to use (e.g. `us915_0`, `au915_0`, `in865`, ...).

#### ChirpStack Gateway Bridge (Basics Station)

Within the `docker-compose.yml` file, you must update the configuration file
that the ChirpStack Gateway Bridge instance must used. The default is
`chirpstack-gateway-bridge-basicstation-eu868.toml`. For available
configuration files, please see the `configuration/chirpstack-gateway-bridge`
directory.

# Data persistence

PostgreSQL and Redis data is persisted in Docker volumes, see the `docker-compose.yml`
`volumes` definition.

## Requirements

Before using this `docker-compose.yml` file, make sure you have [Docker](https://www.docker.com/community-edition)
installed.

## Certificados CA (gateway y application)

Para poder usar **Get Certificate** en la UI (certificados de gateway y de integración MQTT por application), hace falta una CA. **Un solo comando** deja todo listo:

**Windows (PowerShell):**
```powershell
.\scripts\setup-certificates-complete.ps1
```

**Linux / macOS:**
```bash
make setup-certificates-complete
```
o `sh scripts/setup-certificates-complete.sh`

El script genera la CA (`ca.pem`, `ca-key.pem`) en `configuration/chirpstack/` si no existe y reinicia ChirpStack. Requiere Docker.

*Alternativa manual:* `.\scripts\generate-ca.ps1` (o `make generate-ca`) y luego `docker compose restart chirpstack`.

## Conectar a MQTT

ChirpStack publica eventos de dispositivos (uplinks, join, etc.) al broker MQTT (Mosquitto en el puerto **1883**). Para conectarte desde tu aplicación o para usar un broker externo, ver **[docs/MQTT-CONEXION.md](docs/MQTT-CONEXION.md)**:

- **Recibir datos**: suscribirse a `application/<APPLICATION_ID>/device/+/event/up` (o `/#`) en `localhost:1883`.
- **Enviar downlink**: publicar en `application/<APPLICATION_ID>/device/<DEV_EUI>/command/down`.
- **Broker externo**: configurar `server` (y opcionalmente usuario/contraseña) en `configuration/chirpstack/chirpstack.toml` y reiniciar ChirpStack.

Si tu **proveedor** (p. ej. Hong GPS / Milesight) te da un broker y tópicos para downlinks, ver **[docs/DOWNLINK-PROVEEDOR-HONG-GPS.md](docs/DOWNLINK-PROVEEDOR-HONG-GPS.md)**. El servicio **mqtt-bridge-provider** en el compose reenvía los downlinks de ChirpStack a ese broker (configurable por variables de entorno).

## Despliegue (Dokploy) y puertos

Si desplegás en **Dokploy** y los puertos **80** o **8080** están en uso, podés cambiar los puertos publicados con variables de entorno (ver **[docs/DEPLOY-DOKPLOY.md](docs/DEPLOY-DOKPLOY.md)**):

- `CHIRPSTACK_UI_PORT` (por defecto 8080) → ej. 8081
- `CHIRPSTACK_REST_PORT` (por defecto 8090) → ej. 8091
- `MOSQUITTO_PORT` (por defecto 1883)

Copiá `.env.example` a `.env` y ajustá los valores, o configuralos en el panel de Dokploy. **Qué subir y qué no** (certificados, secretos) está documentado en ese mismo doc.

## Importing device repository

To import the [lorawan-devices](https://github.com/TheThingsNetwork/lorawan-devices)
repository (optional step), run the following command:

```bash
make import-lorawan-devices
```

This will clone the `lorawan-devices` repository and execute the import command of ChirpStack.
Please note that for this step you need to have the `make` command installed.

**Note:** an older snapshot of the `lorawan-devices` repository is cloned as the
latest revision no longer contains a `LICENSE` file.

## Usage

To start the ChirpStack simply run:

```bash
$ docker compose up
```

After all the components have been initialized and started, you should be able
to open http://localhost:8080/ in your browser.

##

The example includes the [ChirpStack REST API](https://github.com/chirpstack/chirpstack-rest-api).
You should be able to access the UI by opening http://localhost:8090 in your browser.

**Note:** It is recommended to use the [gRPC](https://www.chirpstack.io/docs/chirpstack/api/grpc.html)
interface over the [REST](https://www.chirpstack.io/docs/chirpstack/api/rest.html) interface.
