# Faqture API - Gemini Context

## Project Overview

`faqture-api` is a continuous Python background service designed for processing and synchronizing commercial documents (invoices, sales notes, credit notes, cancellations, delivery guides) with an external REST API, primarily for electronic billing purposes (tailored for SUNAT regulations in Peru, based on IGV, RUC/DNI, and PE country codes). 

The service polls a local PostgreSQL database for pending or un-processed documents, constructs the required JSON payloads, sends them to the external electronic billing API, and updates the local database with the processing status. It also includes an automated database backup scheduling system with optional Google Drive integration.

## Main Technologies

*   **Language:** Python 3
*   **Database:** PostgreSQL (`psycopg2`)
*   **HTTP Client:** `requests` (for REST API communication)
*   **Backups:** `pg_dump`, `google_api_python_client` (Google Drive)
*   **Configuration:** `configparser` (INI files)
*   **Packaging:** PyInstaller (indicated by `Faqture.spec`)

## Architecture & Directory Structure

*   **`main.py`:** The entry point of the application. It runs a continuous loop (`ProcessManager`) that orchestrates the data extraction, API transmission, and database backups based on toggles defined in the configuration.
*   **`config.py` & `config.ini`:** Centralized configuration management. Controls database credentials, backup schedules (`BU_TIME`, `BU_TIME2`), and feature toggles (`M_DOC`, `M_ANUL`, `M_NCREDI`, etc.) to enable/disable specific document processing flows.
*   **`api/api.py`:** Contains the `ApiClient` which handles the HTTP POST/PUT requests to the external billing API. It handles success/error responses and triggers database updates to reflect the new state (e.g., updating with an `external_id` or marking as 'PROCESADO').
*   **`models/comercial/`:** Contains the data access layer. Modules like `models.py` execute SQL queries to fetch pending documents from the PostgreSQL database (`comercial.ventas`, `comercial.detalle_venta`, etc.) and transform them into structured Python dictionaries representing the expected JSON format for the external API.
*   **`base/comercial/db.py`:** (Inferred) Contains the actual database connection and update operations (e.g., `update_venta_pgsql`).
*   **`base/backup/`:** Contains the logic for scheduled database backups (`backup.py` using `pg_dump` and gzip) and uploading to Google Drive (`send_drive.py`).

## Building and Running

### Prerequisites
*   Python 3.x installed.
*   PostgreSQL tools installed (specifically `pg_dump` in the system PATH if backups are enabled).
*   A correctly configured `config.ini` file in the root directory.

### Setup Environment
1.  Create and activate a virtual environment (optional but recommended).
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Execution
Run the main script to start the background polling service:
```bash
python main.py
```

### Packaging
The project uses PyInstaller to build a standalone executable. To build:
```bash
pyinstaller Faqture.spec
```

## Development Conventions

*   **Error Handling:** The system relies heavily on `try...except` blocks in the main loop to ensure continuous operation even if a specific API call or database read fails, logging the errors appropriately via `logger.log`.
*   **Modularity:** The processing flows are separated logically by document type (e.g., `leer_db` for documents, `leer_db_anulados` for cancellations).
*   **API Security:** It uses a Bearer token for authorization, which is read from the database (`read_empresa_pgsql`). It currently disables SSL verification warnings (`verify=False` in requests).
