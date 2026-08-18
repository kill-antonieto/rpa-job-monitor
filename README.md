# RPA Job Monitor

CLI ligera para registrar ejecuciones de bots RPA, detectar errores y consultar indicadores operativos desde una base SQLite local.

## Qué resuelve

- Catálogo de bots, propietarios y frecuencia prevista.
- Registro de ejecuciones exitosas, fallidas o con advertencias.
- Resumen de los últimos 30 días con tasa de éxito y duración promedio.
- Sin dependencias externas ni datos enviados a terceros.

## Uso

```powershell
python rpa_monitor.py add-job "Factura proveedor" --owner "Operaciones" --schedule "Lun-Vie 08:00"
python rpa_monitor.py record "Factura proveedor" success --duration 42 --notes "120 facturas procesadas"
python rpa_monitor.py dashboard
```

La base se guarda en `rpa-monitor.db`, que no se versiona.

## Próximas mejoras

- Importar ejecuciones desde UiPath, Power Automate o Automation Anywhere.
- Exportar el panel a CSV.
- Enviar alertas cuando un bot falle varias veces.
