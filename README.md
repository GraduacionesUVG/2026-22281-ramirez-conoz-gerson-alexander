# CONGENIA: Módulo de Arquitectura y Servicios

Sistema de apoyo a la decisión clínica para la sospecha de condiciones genéticas pediátricas mediante inteligencia artificial y análisis de datos clínicos en el Hospital Regional de Cobán.

Trabajo de graduación de la Licenciatura en Ingeniería en Ciencias de la Computación y Tecnologías de la Información, Universidad del Valle de Guatemala, 2026.

## Descripción

El Hospital Regional de Cobán no tiene un registro estructurado de pacientes pediátricos y neonatales con sospecha de condiciones genéticas. Su sistema hospitalario, el SADC, no captura signos de alerta, fenotipos ni antecedentes familiares, así que esas sospechas pueden perderse entre una atención y otra.

CONGENIA es una plataforma integrada al SADC para registrar, gestionar y analizar tempranamente esas sospechas. Este repositorio contiene el **módulo de Arquitectura y Servicios**: la plataforma que sostiene el registro clínico, su integración con el SADC y la infraestructura en AWS sobre la que opera.

### Funcionamiento

1. **Identificación.** El médico inicia sesión (Keycloak, OpenID Connect) y busca al paciente por número de historia clínica. La API consulta el SADC y precarga los datos del paciente en la ficha.
2. **Captura de la ficha genética.** Desde el navegador del teléfono, el médico completa los datos de la consulta, los antecedentes familiares, los signos de alerta (con fotografía clínica por región anatómica), los estudios de gabinete y las observaciones. El estado parcial de la captura se guarda en Redis.
3. **Consentimiento informado.** El padre, la madre o el representante legal firma en pantalla. Las fotografías y la firma se suben directamente a almacenamiento S3 cifrado, fuera de la base de datos relacional.
4. **Procesamiento en segundo plano.** Al guardar la ficha, la API publica un mensaje en RabbitMQ y un trabajador independiente genera el PDF del consentimiento. Si el trabajador se detiene, el registro sigue funcionando.
5. **Adendas.** Una ficha guardada no se modifica: las correcciones y los hallazgos nuevos se agregan como adendas trazables, que el médico asignado revisa.
6. **Consulta y análisis.** El panel web permite buscar fichas, revisar las sugerencias CIE-10 y consultar la reportería. Estos dos últimos componentes analíticos pertenecen a otros módulos del proyecto.

### Resultados principales

- **Prueba piloto en el hospital**, con siete pediatras y el SADC real: se registraron las 21 operaciones requeridas y ninguna de las 14 tareas observadas se interrumpió.
- **Campaña de carga sintética** de seis escenarios, con un pico de 18 médicos simultáneos: se registraron las 352 capturas y los 352 consentimientos obtuvieron su PDF verificado. La API respondió a todas las sondas de preparación durante 30 minutos.
- **Infraestructura reproducible.** La plataforma completa se replicó en otra cuenta de AWS a partir de la misma definición de Terraform, sin configurar ningún recurso a mano.

## Tecnologías utilizadas

| Capa | Tecnologías |
|---|---|
| Interfaz (ficha y panel de consulta) | React, Vite, TypeScript, oidc-client-ts, Recharts; servida por nginx |
| API clínica | Node.js 22, Express (JavaScript), pg, amqplib, jose, AWS SDK S3, Scalar (documentación OpenAPI) |
| Trabajador de PDF | Node.js, TypeScript, PDFKit, zod |
| Persistencia | PostgreSQL 16 (Amazon RDS) |
| Estado temporal de captura | Redis 7 (Amazon ElastiCache) |
| Identidad y permisos | Keycloak 26 (OpenID Connect, roles por realm) |
| Mensajería | RabbitMQ 3.13 |
| Archivos | Almacenamiento compatible con S3 (SeaweedFS en local, Amazon S3 en producción) |
| Orquestación local | Docker, Docker Compose |
| Infraestructura | Terraform, AWS (VPC, ECS Fargate, ALB, WAF, Route 53, ACM, Cloud Map, Secrets Manager, CloudWatch, ECR) |
| Entrega continua | GitHub Actions con OIDC hacia AWS |
| Pruebas de carga | k6, Grafana |

## Requisitos previos

**Ejecución local**
- Git
- Docker 24.0 o superior y Docker Compose v2.20 o superior
- Unos 8 GB de RAM libres para Docker (el stack levanta 9 contenedores)
- Solo para desarrollar un servicio fuera de los contenedores: Node.js 22 y pnpm 11 (interfaz) o npm (API y trabajador)

**Despliegue en AWS (opcional)**
- Terraform 1.10 o superior
- AWS CLI v2 con credenciales de una cuenta propia
- `jq`, `curl`, Bash y GNU Make
- Un dominio administrado en Route 53

## Estructura del repositorio

```
.
├── capturas/            Capturas de pantalla del sistema (captura-01 … captura-12)
├── demo/demo.mp4        Video demostrativo con narración
├── docs/
│   ├── informe_final.pdf
│   └── consentimiento_firmado.pdf
├── src/                       Orquestación local (repositorio CONGENIA-ORCH)
│   ├── docker-compose.yml     Stack completo para desarrollo local
│   ├── .env.example           Variables de entorno con valores de desarrollo
│   ├── keycloak/              Imagen de Keycloak con el realm congenia
│   ├── scripts/               Verificación de salud y publicación de imágenes
│   ├── CONGENIA-M1/           Interfaz: ficha y panel de consulta
│   ├── CONGENIA-M1-SERVER/    API del registro y de la consulta, esquema y migraciones
│   ├── CONGENIA-M1-PDF-WORKER/ Trabajador que genera el PDF del consentimiento
│   └── CONGENIA-INFRA/        Infraestructura como código en Terraform (AWS)
└── README.md
```

El código proviene de cinco repositorios privados de la organización CONGENIAGT, copiados en su última versión sin el historial de git. La raíz de `src/` es el orquestador, porque su `docker-compose.yml` construye cada servicio desde las subcarpetas. Las imágenes que corrieron en producción corresponden a estas versiones: interfaz `1.0.0-2be5349`, API `1.0.0-50d4a4d` y trabajador `1.0.0-a2fbcdb` (Cuadro 6 del informe). En la documentación y las pruebas de `CONGENIA-INFRA` se reemplazó el identificador real de la cuenta de AWS por un valor ficticio.

## Instalación

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/GraduacionesUVG/2026-22281-ramirez-conoz-gerson-alexander.git
   cd 2026-22281-ramirez-conoz-gerson-alexander
   ```

2. **Instalar dependencias.** Cada servicio instala sus dependencias dentro de su propia imagen de Docker, así que no hace falta ejecutar `npm install` en la raíz. Para desarrollar un servicio fuera de los contenedores:

   ```bash
   cd src/CONGENIA-M1-SERVER && npm install
   ```

3. **Configurar las variables de entorno**

   ```bash
   cp src/.env.example src/.env
   # Edita src/.env con tus propios valores
   ```

4. **Ejecutar el proyecto**

   ```bash
   cd src/CONGENIA-ORCH
   docker compose up -d --build         # equivalente: npm start
   ```

   La interfaz queda disponible en `http://localhost:<PUERTO_FRONTEND>`.

## Capturas

Hay 12 capturas en [`/capturas`](capturas/). Las tomas del teléfono se hicieron durante una prueba en el dominio de pruebas `cogenia.app`. El nombre del paciente consultado en el SADC está pixelado, y las tomas de escritorio ocultan los datos clínicos.

| # | Pantalla |
|---|---|
| [01](capturas/captura-01.png) | Inicio de sesión |
| [02](capturas/captura-02.png) | Búsqueda del paciente en el SADC por historia clínica |
| [03](capturas/captura-03.png) | Ficha genética: secciones por completar |
| [04](capturas/captura-04.png) | Consentimiento informado: declaración y autorizaciones |
| [05](capturas/captura-05.png) | Consentimiento: firma del representante legal |
| [06](capturas/captura-06.png) | Signo de alerta con fotografía del hallazgo (imagen de prueba) |
| [07](capturas/captura-07.png) | Confirmación de la ficha guardada |
| [08](capturas/captura-08.png) | Adenda: reemplazo de un estudio existente |
| [09](capturas/captura-09.png) | Adenda enviada a revisión |
| [10](capturas/captura-10.png) | Panel web: búsqueda de fichas clínicas |
| [11](capturas/captura-11.png) | Panel web: revisión del lote de sugerencias CIE-10 |
| [12](capturas/captura-12.png) | Panel web: reportería con el agente de datos |

## Demo

[`/demo/demo.mp4`](demo/demo.mp4): recorrido narrado de unos 10 minutos (H.264, 1080×1350) por la ficha genética, las adendas, la corrección CIE-10 y la reportería.

## Documentación

- [Informe final](docs/informe_final.pdf)
- [Consentimiento de uso de foto y video firmado](docs/consentimiento_firmado.pdf)

## Autores

- **Gerson Alexander Ramírez Conoz**, carné 22281. Módulo de Arquitectura y Servicios.

CONGENIA se desarrolló en equipo. Los demás módulos estuvieron a cargo de Madeline Castro, Xavier López y Josué Marroquín. Asesoría: Dr. Marco Paez, Ing. Oscar Iván Robles e Ing. Gabriel Brolo Tobar.

## Licencia

Todos los derechos reservados. Este código se publica solo para la evaluación del trabajo de graduación en la Universidad del Valle de Guatemala; no se concede permiso para usarlo, copiarlo, modificarlo ni distribuirlo sin la autorización escrita del autor.
