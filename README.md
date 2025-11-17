
# 🚀 **Tatvix – Legal Assistant API**

Your personal AI-powered legal agent designed to help you understand the law in the simplest and most intuitive way.

This project is currently in **local development** and runs entirely on your machine.

---

# 🧱 **Prerequisites (Windows Only)**

Before installing or running the system, ensure the following dependencies are installed on your Windows machine.

---

## ✅ **1. Install Python & pip**

Tatvix requires:

* **Python 3.10+**
* **pip package manager** (comes with Python)

### ✔ Check Installation

Open PowerShell or CMD and run:

```bash
python --version
pip --version
```

If not installed, download Python from:

👉 [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)

During installation, **make sure to enable:**

✔ *“Add Python to PATH”*
✔ *“Install pip”*

---

## ✅ **2. Install MongoDB (Windows)**

Tatvix uses MongoDB for storing original legal documents.

Download MongoDB Community Server:

👉 **[https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)**

### ✔ Choose the **`.msi` installer**

(It handles everything needed for Windows)

### ✔ After installation, add MongoDB to PATH:

1. Open **System Properties → Environment Variables**
2. Under **System variables → Path** → click **Edit**
3. Add:

```
C:\Program Files\MongoDB\Server\7.0\bin
```

This enables commands like:

```
mongod
mongo
```

(Optional but recommended) Install **MongoDB Compass** for GUI browsing.

---

## ✅ **3. Install Tesseract OCR (Windows)**

Tatvix uses Tesseract for OCR when extracting text from scanned PDFs.

Download the Windows installer from:

👉 **[https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)**

Then download this file (latest stable at the time of writing):

```
tesseract-ocr-w64-setup-5.5.0.20241111.exe
```

Install it normally.

### ✔ Add Tesseract to PATH:

1. Navigate to:

   ```
   C:\Program Files\Tesseract-OCR
   ```
2. Copy the folder path
3. Add it to **System Environment Variables → Path**

Now verify:

```bash
tesseract --version
```

---


# 📦 **Setup & Installation**

## 1. **Clone the Repository**

```bash
git clone <public_repo_link>
```

> *(Repository not public yet)*

---

# ⚙️ **Environment Setup**

Create a `.env` file in the root directory with the following variables:

```env
SQLITE_DB_NAME="TatvixDB.db"
JWT_SECRET_KEY="your_secret_key_here"
ENC_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGIN="http://localhost:5173"
MONGODB_URI="mongodb://localhost:27017/TatvixDb"
WEAVIATE_SERVER="http://localhost:8081/vectors"
GOOGLE_API_KEY="your_google_api_key_here"
MCP_SERVER="http://localhost:5050/mcp"
```

### **Important Notes**

* Generate a strong JWT secret via: [https://jwtsecrets.com](https://jwtsecrets.com)
* Google API key → create in **Google AI Studio**
* Supported LLMs → **Gemini 2.5 Flash / Pro**
* Uses:

  * SQLite (local user/session storage)
  * MongoDB (document store)
  * Weaviate (vector DB)
  * Local inference server (Gemma 300M embeddings)

---

# 🐳 **Docker & Model Setup**

Before running the system:

## 1. **Start Docker Desktop**

Weaviate and the embedding inference container require Docker to be running.

---

## 2. **Install the Embedding Model (Gemma 300M)**

Tatvix uses **Gemma 300M Embedding Model**, optimized for edge devices.

Inside the folder:

```
TatvIX_API/Transformer_Inference_API/
```

Run this Python snippet to download the model:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/embeddinggemma-300M",
    local_dir="./models/gemma-300m",
    local_dir_use_symlinks=False
)
```

Your final directory structure must look like:

```
TatvIX_API/
└── Transformer_Inference_API/
    └── models/
        └── gemma-300m/   <-- model files here
```

This folder is mounted by the inference Docker container at runtime.

---

## 3. **Run the Setup Script**

After Docker is running and the model is installed:

```bash
C:\<path_to_project>\TatvIX_API\setup.bat
```

Follow the on-screen instructions.

### ⚠️ *Note:*

Always run option 1, to start weaviate database, before running any of the other options, it has direct dependency on it.

---

# 🗃️ **Setup Server — Document Ingestion Layer**

The setup server handles:

✔ Document upload
✔ MongoDB storage
✔ Chunking & embedding generation
✔ Pushing embeddings into Weaviate

### ⚠️ *Note:*

Avoid huge files unless your system has enough RAM to perform embedding inference.

---

# 🔌 **Setup API – Endpoints**

Use **Postman** to interact with ingestion endpoints.

---

## **1. Upload Documents → MongoDB**

```
POST http://localhost:5000/populate-mongodb
```

**Body → form-data**

* `file`: list of files (PDF/text documents)

---

## **2. Populate Vector DB (Weaviate)**

```
POST http://localhost:5000/populate-weaviate
```

No body required.
Uses documents already stored in MongoDB.

---

## **3. Drop Weaviate Database**

```
POST http://localhost:5000/drop-weaviate-db
```

⚠️ **Warning:** Deletes all embeddings & vectors.

---

# 🧠 **Application Server (Main API)**

This server handles:

* Authentication
* Chat sessions
* Legal agent responses
* Retrieval-augmented generation
* MCP-based document search

To explore the APIs interactively:

```
http://localhost:8000/docs
```

Powered by **FastAPI Swagger UI**.

