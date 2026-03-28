# SV DTE ERPNext

El Salvador DTE (Documento Tributario Electronico) module for ERPNext v16. Integrates with the Ministerio de Hacienda (MH) API to electronically sign and transmit tax documents.

## Supported Document Types

| Code | Type | Description |
|------|------|-------------|
| `01` | Factura | Consumer invoice (IVA-inclusive prices) |
| `03` | Credito Fiscal (CCF) | B2B tax credit invoice (IVA-exclusive prices) |
| `05` | Nota de Credito | Credit note |
| `06` | Nota de Debito | Debit note |
| `43` | Factura de Exportacion | Export invoice |
| `44` | Factura Sujeto Excluido | Exempt subject invoice |

Currently implemented builders: **Factura (01)** and **Credito Fiscal (03)**.

## How It Works

```
Sales Invoice (submitted)
        |
        v
  Create DTE Document (auto-generates UUID + numero de control)
        |
        v
  Build JSON (constructs MH-compliant JSON from invoice data)
        |
        v
  Sign (sends JSON to local firmador service, returns JWS)
        |
        v
  Transmit to MH API (sends signed JWS to Ministerio de Hacienda)
        |
        v
  Accepted (sello de recepcion stored) / Rejected (error details stored)
```

Each step is tracked on the DTE Document with full audit logging in DTE API Log.

## Requirements

### ERPNext / Frappe

- ERPNext v16
- Frappe v16
- Python 3.10+

### MH Credentials

You need an active account with the Ministerio de Hacienda DTE system:

- **NIT** (14 digits, no hyphens) and **NRC** (with hyphen) of the emisor
- **API password** provided by MH for DTE transmission
- **Digital certificate** (.crt) issued by DGII for document signing
- **Certificate private key password**

Register at https://admin.factura.gob.sv/

### Firmador (Signing Service)

The MH requires documents to be digitally signed before transmission. The firmador is a local service that handles cryptographic signing:

**Option A: Official DTE-Firmador (Windows)**
- Download from https://factura.gob.sv/informacion-tecnica-y-funcional/
- Runs as a Windows service on port 8113

**Option B: SVFE-API-Firmador (Docker / Linux)**
- https://github.com/cvjuan270/svfe-api-firmador
- Runs in Docker on port 8113

The firmador must be reachable from your ERPNext server at `http://localhost:8113/firmardocumento/` (configurable).

Place your certificate at `certificados/<NIT>.crt` in the firmador's working directory.

## Installation

```bash
# From your bench directory
bench get-app /path/to/sv_dte_erpnext
# Or directly from GitHub
bench get-app https://github.com/sovITxyz/sv_dte_erpnext.git

bench --site <your-site> install-app sv_dte

bench --site <your-site> migrate
```

## Configuration

### 1. SV DTE Settings

Navigate to **SV DTE Settings** in the sidebar or search bar. Fill in:

**Environment**
- `Ambiente`: `00` for testing, `01` for production
- `Firmador URL`: URL to your firmador service (default: `http://localhost:8113/firmardocumento/`)

**MH Authentication**
- `NIT`: Your 14-digit NIT (e.g. `06141234567890`)
- `API Password`: The password provided by MH
- `NRC`: Your NRC with hyphen (e.g. `1234-5`)
- `Certificate Password`: Private key password for the firmador

**Emisor (Issuer)**
- `Nombre Emisor`: Legal company name
- `Nombre Comercial`: Trade name
- `Codigo Actividad Economica`: CIIU code (e.g. `46100`)
- `Descripcion Actividad`: Activity description

**Establecimiento**
- `Tipo Establecimiento`: `01` = Casa Matriz, `02` = Sucursal
- `Cod Establecimiento MH` / `Cod Punto Venta MH`: Codes assigned by MH (default `0000`)

**Direccion**
- `Departamento`: Department code (e.g. `06` = San Salvador)
- `Municipio`: Municipality code
- `Complemento Direccion`: Street address

**Contacto**
- `Telefono` and `Correo Electronico`

### 2. Customer Custom Fields (Optional)

For CCF documents, receptor details are pulled from the DTE Document form. To auto-populate from Customer records, add these custom fields to the Customer doctype:

| Field | Fieldname | Type |
|-------|-----------|------|
| NIT | `sv_nit` | Data |
| NRC | `sv_nrc` | Data |
| Cod Actividad | `sv_cod_actividad` | Data |
| Desc Actividad | `sv_desc_actividad` | Data |
| Nombre Comercial | `sv_nombre_comercial` | Data |
| Departamento | `sv_departamento` | Data |
| Municipio | `sv_municipio` | Data |
| Direccion Complemento | `sv_direccion_complemento` | Small Text |

## Usage

### From Sales Invoice

1. Submit a Sales Invoice
2. Click **El Salvador DTE > Create DTE**
3. Select the DTE type (CCF, Factura, etc.)
4. Enter the receptor NIT, NRC, and email
5. Click **Create** - this opens the DTE Document

### From DTE Document

**Step by step:**
1. Click **Actions > Build JSON** - generates the MH-compliant JSON payload
2. Click **Actions > Sign** - sends to firmador, stores the JWS
3. Click **Actions > Transmit to MH** - sends to MH API

**One click:**
- Click **Build, Sign & Transmit** to do all three steps at once

### Checking Status

- `Accepted`: MH returned a sello de recepcion (stored on the document)
- `Rejected`: Check `MH Response JSON` section for error details
- All API calls are logged in **DTE API Log**

### Invalidation

To invalidate an accepted DTE, use the API directly:

```python
from sv_dte.sv_dte.api.transmission import invalidate_document

dte = frappe.get_doc("DTE Document", "<codigo_generacion>")
result = invalidate_document(dte, reason="Error en datos del receptor")
```

## MH API Endpoints

| Purpose | Testing | Production |
|---------|---------|------------|
| Auth | `https://apitest.dtes.mh.gob.sv/seguridad/auth/` | `https://api.dtes.mh.gob.sv/seguridad/auth/` |
| Reception | `https://apitest.dtes.mh.gob.sv/fesv/recepciondte` | `https://api.dtes.mh.gob.sv/fesv/recepciondte` |
| Invalidation | `https://apitest.dtes.mh.gob.sv/fesv/anulardte` | `https://api.dtes.mh.gob.sv/fesv/anulardte` |
| Batch | `https://apitest.dtes.mh.gob.sv/fesv/recepcionlote/` | `https://api.dtes.mh.gob.sv/fesv/recepcionlote/` |

JWT tokens are cached automatically (48h testing, 24h production).

## Testing with MH

Before going to production, MH requires 50-90 successful test transmissions per DTE type in the testing environment (`ambiente = 00`). Use `https://apitest.dtes.mh.gob.sv` to validate your integration.

Verify accepted documents at: https://admin.factura.gob.sv/consultaPublica

## DocTypes

| DocType | Type | Purpose |
|---------|------|---------|
| SV DTE Settings | Single | API credentials, emisor config, firmador settings |
| DTE Document | Regular | One per DTE - tracks lifecycle, stores JSON payloads and MH responses |
| DTE API Log | Regular | Audit log of every API call (auth, sign, transmit) |

## Project Structure

```
sv_dte/
├── hooks.py                          # App config, Sales Invoice JS hook
├── modules.txt
├── public/js/
│   └── sales_invoice.js              # "Create DTE" button on Sales Invoice
└── sv_dte/
    ├── api/
    │   ├── __init__.py               # create_dte_from_invoice whitelisted API
    │   ├── auth.py                   # MH JWT authentication
    │   ├── signing.py                # Local firmador integration
    │   ├── transmission.py           # MH document transmission & invalidation
    │   └── dte_builder.py            # JSON payload builders (CCF, Factura)
    └── doctype/
        ├── sv_dte_settings/          # Settings doctype
        ├── dte_document/             # DTE document doctype + JS form
        └── dte_api_log/              # API audit log doctype
```

## License

AGPL-3.0-or-later
