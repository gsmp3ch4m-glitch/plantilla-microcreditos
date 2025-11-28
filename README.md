# El Canguro Pro - Plantilla Casa de Empeño y Microcrédito v1.0

Sistema de gestión integral para casa de empeño y microcréditos desarrollado en Python con interfaz gráfica Tkinter.

## Características

- **Gestión de Clientes**: Registro completo de clientes con datos personales y documentación
- **Módulos de Préstamo**:
  - Casa de Empeño
  - Préstamo Bancario Programado
  - Rapidario
- **Gestión de Caja**: Control de pagos y cronogramas
- **Generación de Documentos**: Contratos y documentos legales en PDF
- **Análisis**: Reportes y análisis de operaciones
- **Sistema de Usuarios**: Control de acceso con roles

## Requisitos

- Python 3.8 o superior
- Tkinter
- Pillow
- tkcalendar
- ReportLab (para generación de PDFs)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/TU_USUARIO/plantilla-casa-empeno-microcredito.git
cd plantilla-casa-empeno-microcredito
```

2. Crea y activa el entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # En Windows PowerShell
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación:
```bash
python src/main.py
```

## Estructura del Proyecto

```
plantilla casa de empeño y microcreditos/
├── src/
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── database/            # Gestión de base de datos
│   ├── ui/                  # Interfaces gráficas
│   ├── utils/               # Utilidades y helpers
│   └── models/              # Modelos de datos
├── .venv/                   # Entorno virtual (no incluido en repo)
├── requirements.txt         # Dependencias del proyecto
└── README.md               # Este archivo
```

## Autor

Edgar Tucno - gsmp3ch4m@gmail.com

## Versión

1.0 - Versión inicial estable

## Licencia

Todos los derechos reservados © 2025
