# Consulta al proveedor – Conexión MQTT para downlinks

Puedes copiar o adaptar el texto siguiente para enviarlo a tu proveedor (Hong GPS / Milesight) y que te confirmen los datos exactos de conexión MQTT.

---

## Mensaje sugerido

**Asunto:** Datos exactos de conexión MQTT (broker para downlinks)

Hola,

Necesito conectar un cliente MQTT a su broker para enviar downlinks a los dispositivos según la documentación que nos compartieron:

- **Broker:** lora.honggps.com  
- **Puerto:** 8884  
- **Client ID:** mqttx_b3d78c78  
- **Tópico downlink:** /Milesight/Downlink/<EUI>

Al intentar conectar desde nuestro servidor (Python/paho-mqtt) recibimos **error de SSL/TLS** (“Unexpected EOF while reading”) y no logramos establecer la conexión. Ya probamos varias combinaciones sin éxito:

- Puerto **8884** con TLS y con WebSockets (WSS)
- Puerto **8883** (MQTT sobre TLS)
- Puerto **1883** (MQTT sin TLS)
- Puertos **8084, 8083, 8080** (WebSocket y TLS)
- Puerto **443** (WSS)

Por favor, ¿pueden confirmar o corregir lo siguiente?

1. **Puerto correcto** para enviar downlinks por MQTT (¿8884, 8883, 1883 u otro?).
2. **Tipo de conexión** en ese puerto:
   - MQTT directo sobre TCP
   - MQTT sobre TLS (certificado)
   - MQTT sobre WebSockets (ws o wss)
3. Si hace falta **usuario y contraseña** MQTT (y cómo se configuran).
4. Si hace falta **certificado cliente** o **CA** para TLS y cómo obtenerlos.
5. Si el **Client ID** debe ser exactamente el que nos dieron o si podemos usar otro (por ejemplo uno propio para nuestro servidor).
6. Algún **ejemplo de conexión** (por ejemplo con MQTTX, mosquitto_pub o código) que funcione contra su broker, para replicar la configuración.

Con esos datos podremos conectar correctamente y enviar los downlinks desde nuestro sistema.

Gracias.

---

## Checklist rápido (para no olvidar preguntar)

- [ ] Puerto exacto (8884 u otro)
- [ ] ¿TLS sí o no? ¿Qué puerto es con TLS y cuál sin?
- [ ] ¿WebSockets (ws/wss) o solo MQTT sobre TCP?
- [ ] Usuario y contraseña MQTT (si aplica)
- [ ] Certificados (CA, cliente) si usan TLS con certificados
- [ ] Client ID: ¿fijo o podemos usar el nuestro?
- [ ] Ejemplo de conexión que funcione (herramienta o código)
