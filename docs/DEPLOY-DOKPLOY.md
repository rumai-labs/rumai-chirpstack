# Despliegue en Dokploy y qué subir / no subir

## Puertos (80, 8080 en uso)

Si en el servidor **80** o **8080** están ocupados, configurá los puertos publicados por variables de entorno.

En **Dokploy** (o en un `.env` junto al `docker-compose.yml`):

| Variable | Por defecto | Ejemplo si 8080 ocupado |
|----------|-------------|--------------------------|
| `CHIRPSTACK_UI_PORT` | 8080 | 8081 |
| `CHIRPSTACK_REST_PORT` | 8090 | 8091 |
| `MOSQUITTO_PORT` | 1883 | 1883 (o otro si hace falta) |

Ejemplo `.env` para Dokploy cuando 8080 y 8090 están usados:

```env
CHIRPSTACK_UI_PORT=8081
CHIRPSTACK_REST_PORT=8091
```

La UI de ChirpStack quedará en `http://tu-servidor:8081` y la REST API en el puerto 8091. El puerto **80** no lo usa este stack; si usás un reverse proxy (Nginx, Traefik) en 80/443, apuntalo al puerto que hayas puesto en `CHIRPSTACK_UI_PORT`.

---

## Qué SÍ subir al repo (staging → producción)

- `docker-compose.yml`
- `configuration/` (chirpstack, chirpstack-gateway-bridge, mosquitto, postgresql/initdb) **excepto** los `.pem` (ver abajo)
- `scripts/`
- `docs/`
- `Makefile`, `README.md`, `.env.example`
- `.gitignore`

---

## Qué NO subir

- **`configuration/chirpstack/ca.pem`** y **`configuration/chirpstack/ca-key.pem`**  
  Son los certificados CA generados por `scripts/setup-certificates-complete.ps1`. Están en `.gitignore`. En el servidor (Dokploy) generarlos o copiarlos aparte y montarlos donde corresponda.

- **`.env`**  
  Si usás `.env` con contraseñas o puertos locales, no lo subas (ya está ignorado con `.*`). En Dokploy configurá las variables en el panel de la aplicación.

- **Secret de ChirpStack**  
  En `configuration/chirpstack/chirpstack.toml` está `secret="you-must-replace-this"`. En producción reemplazalo por un valor seguro (o inyectalo por variable de entorno si ChirpStack lo permite) y no subas ese valor al repo.

- **Contraseñas de Postgres**  
  En el compose están por defecto (`POSTGRES_PASSWORD=chirpstack`). Para producción conviene usar secrets de Dokploy o variables de entorno y no commitear contraseñas reales.

---

## Resumen rápido

| Qué | ¿Subir? |
|-----|---------|
| Código, compose, configs (sin .pem) | Sí |
| `ca.pem`, `ca-key.pem` | No (generar en el servidor o subir por canal seguro) |
| `.env` con secretos/puertos locales | No |
| Secret de ChirpStack en producción | Cambiar y no subir el valor real |
| Puertos 8080/8090 ocupados | Usar `CHIRPSTACK_UI_PORT` y `CHIRPSTACK_REST_PORT` en Dokploy (o `.env`) |
