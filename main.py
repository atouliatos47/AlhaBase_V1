# main.py - AlphaBase v4.0 (FIXED)
from fastapi import FastAPI, HTTPException, Depends, WebSocket, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
from email_manager import email_manager
import uvicorn
import json
import os

# Import our refactored modules
from models import Base, engine, SessionLocal, UserDB, DataDB, FileDB
from security_rules import security_rules
from query_system import query_parser, query_engine
from file_storage import file_storage
from websocket_manager import manager
from mqtt_manager import mqtt_manager

# FastAPI App
app = FastAPI(title="AlphaBase", version="4.0.0")

# Mount static files for web console
app.mount("/console", StaticFiles(directory="console", html=True), name="console")

# CORS

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import configuration
from config import config

# Security (from config)
SECRET_KEY = config.get("security", "secret_key")
ALGORITHM = config.get("security", "algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = config.get("security", "access_token_expire_minutes")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class DataItem(BaseModel):
    collection: str
    key: str
    value: dict

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "Welcome to AlphaBase v4.0!",
        "status": "running",
        "features": [
            "Authentication", "Persistent Storage", "Real-time WebSockets", 
            "MQTT Integration", "Security Rules", "Query System", "File Storage"
        ],
        "storage": "SQLite Database + File System",
        "timestamp": datetime.now().isoformat()
    }

# Authentication Endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = UserDB(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def get_current_user(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }

# Data Endpoints
@app.post("/data/set")
async def set_data(item: DataItem, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    if not security_rules.validate_write(item.collection, username):
        raise HTTPException(status_code=403, detail=f"Write access denied to collection: {item.collection}")
    
    data_id = f"{item.collection}:{item.key}"
    existing_data = db.query(DataDB).filter(DataDB.id == data_id).first()
    
    if existing_data:
        resource_data = {"owner": existing_data.owner, "id": existing_data.id}
        if not security_rules.validate_write(item.collection, username, resource_data):
            raise HTTPException(status_code=403, detail="Not authorized to update this data")
        existing_data.value = json.dumps(item.value)
        existing_data.owner = username
    else:
        new_data = DataDB(
            id=data_id,
            collection=item.collection,
            key=item.key,
            value=json.dumps(item.value),
            owner=username,
            created_at=datetime.utcnow()
        )
        db.add(new_data)
    
    db.commit()
    await manager.broadcast(json.dumps({"action": "update", "collection": item.collection, "key": item.key}))
    return {"success": True, "collection": item.collection, "key": item.key, "message": "Data stored successfully"}

@app.get("/data/get/{collection}/{key}")
async def get_data(collection: str, key: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    if not security_rules.validate_read(collection, username):
        raise HTTPException(status_code=403, detail=f"Read access denied to collection: {collection}")
    
    data_id = f"{collection}:{key}"
    data = db.query(DataDB).filter(DataDB.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    resource_data = {"owner": data.owner, "id": data.id}
    if not security_rules.validate_read(collection, username, resource_data):
        raise HTTPException(status_code=403, detail="Not authorized to read this data")
    
    return {
        "success": True,
        "collection": collection,
        "key": key,
        "data": json.loads(data.value),
        "owner": data.owner
    }

@app.get("/data/list/{collection}")
async def list_collection(collection: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    if not security_rules.validate_read(collection, username):
        raise HTTPException(status_code=403, detail=f"Read access denied to collection: {collection}")
    
    data_items = db.query(DataDB).filter(DataDB.collection == collection).all()
    filtered_items = {}
    for item in data_items:
        resource_data = {"owner": item.owner, "id": item.id}
        if security_rules.validate_read(collection, username, resource_data):
            filtered_items[item.key] = json.loads(item.value)
    
    return {"success": True, "collection": collection, "count": len(filtered_items), "items": filtered_items}

@app.get("/data/query/{collection}")
async def query_data(collection: str, where: str = None, orderBy: str = None, limit: int = None, 
                    startAfter: str = None, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    if not security_rules.validate_read(collection, username):
        raise HTTPException(status_code=403, detail=f"Read access denied to collection: {collection}")
    
    data_items = db.query(DataDB).filter(DataDB.collection == collection).all()
    query_data = []
    for item in data_items:
        resource_data = {"owner": item.owner, "id": item.id}
        if security_rules.validate_read(collection, username, resource_data):
            query_data.append({
                "key": item.key,
                "data": json.loads(item.value),
                "owner": item.owner,
                "created_at": item.created_at.isoformat()
            })
    
    query_params = {}
    if where: query_params["where"] = where
    if orderBy: query_params["orderBy"] = orderBy
    if limit: query_params["limit"] = limit
    if startAfter: query_params["startAfter"] = startAfter
    
    query = query_parser.parse_query_params(query_params)
    filtered_data = query_engine.apply_where(query_data, query["where"])
    if query["order_by"]:
        filtered_data = query_engine.apply_order_by(filtered_data, query["order_by"])
    if query["limit"]:
        filtered_data = query_engine.apply_limit(filtered_data, query["limit"])
    
    items = {item["key"]: item["data"] for item in filtered_data}
    return {
        "success": True,
        "collection": collection,
        "count": len(filtered_data),
        "query": query,
        "items": items,
        "results": filtered_data
    }

@app.get("/data/collections")
async def list_collections(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """List all collections accessible to the current user"""
    try:
        # Get all unique collections from the database
        data_items = db.query(DataDB.collection).distinct().all()
        
        # Filter collections based on read permissions
        collections = []
        for item in data_items:
            collection = item[0]
            if security_rules.validate_read(collection, username):
                collections.append(collection)
        
        return {
            "success": True,
            "collections": sorted(collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/data/delete/{collection}/{key}")
async def delete_data(collection: str, key: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):

    
    if not security_rules.validate_write(collection, username):
        raise HTTPException(status_code=403, detail=f"Write access denied to collection: {collection}")
    
    data_id = f"{collection}:{key}"
    data = db.query(DataDB).filter(DataDB.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    resource_data = {"owner": data.owner, "id": data.id}
    if not security_rules.validate_write(collection, username, resource_data):
        raise HTTPException(status_code=403, detail="Not authorized to delete this data")
    
    db.delete(data)
    db.commit()
    await manager.broadcast(json.dumps({"action": "delete", "collection": collection, "key": key}))
    return {"success": True, "message": "Data deleted successfully"}

# File Storage Endpoints
@app.post("/storage/upload")
async def upload_file(file: UploadFile = File(...), is_public: str = Form("false"), 
                     username: str = Depends(verify_token), db: Session = Depends(get_db)):
    max_size = 10 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
    
    file_info = await file_storage.save_upload_file(file, username, is_public.lower() == "true")
    file_record = FileDB(
        id=file_info["file_id"],
        filename=file_info["filename"],
        original_filename=file_info["original_filename"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"],
        owner=username,
        is_public=is_public,
        created_at=datetime.utcnow()
    )
    db.add(file_record)
    db.commit()
    
    return {
        "success": True,
        "file_id": file_info["file_id"],
        "filename": file_info["original_filename"],
        "file_size": file_info["file_size"],
        "mime_type": file_info["mime_type"],
        "is_public": file_info["is_public"],
        "download_url": f"/storage/download/{file_info['file_id']}",
        "message": "File uploaded successfully"
    }

@app.get("/storage/download/{file_id}")
async def download_file(file_id: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    file_record = db.query(FileDB).filter(FileDB.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if file_record.is_public != "true" and file_record.owner != username:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type=file_record.mime_type
    )

@app.get("/storage/files")
async def list_files(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    files = db.query(FileDB).filter(FileDB.owner == username).all()
    file_list = []
    for file in files:
        file_list.append({
            "file_id": file.id,
            "filename": file.original_filename,
            "file_size": file.file_size,
            "mime_type": file.mime_type,
            "is_public": file.is_public == "true",
            "created_at": file.created_at.isoformat(),
            "download_url": f"/storage/download/{file.id}"
        })
    return {"success": True, "files": file_list, "count": len(file_list)}

@app.delete("/storage/delete/{file_id}")
async def delete_file(file_id: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    file_record = db.query(FileDB).filter(FileDB.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if file_record.owner != username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    if file_storage.delete_file(file_id, db):
        return {"success": True, "message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")

# Security Rules Endpoints
@app.get("/security/rules")
async def get_security_rules(username: str = Depends(verify_token)):
    return security_rules.rules

@app.post("/security/rules/{collection}")
async def update_security_rule(collection: str, rules: dict, username: str = Depends(verify_token)):
    if collection not in security_rules.rules:
        security_rules.rules[collection] = {}
    if "read" in rules:
        security_rules.rules[collection]["read"] = rules["read"]
    if "write" in rules:
        security_rules.rules[collection]["write"] = rules["write"]
    return {"success": True, "message": f"Rules updated for {collection}"}

# System Endpoints
@app.get("/system/status")
async def system_status(username: str = Depends(verify_token)):
    return {
        "websocket_clients": len(manager.active_connections),
        "mqtt_connected": mqtt_manager.client.is_connected(),
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0"
    }

# Email Notification Endpoints
@app.post("/notifications/send-email")
async def send_email_notification(
    request: dict,
    username: str = Depends(verify_token)
):
    """Send an email notification"""
    to_email = request.get("to_email")
    subject = request.get("subject")
    body = request.get("body")
    
    success = email_manager.send_email(to_email, subject, body)
    return {
        "success": success,
        "message": "Email sent successfully" if success else "Failed to send email"
    }

@app.post("/notifications/send-alert")
async def send_alert_notification(
    request: dict,
    username: str = Depends(verify_token)
):
    """Send a formatted alert email"""
    to_email = request.get("to_email")
    alert_title = request.get("alert_title")
    alert_message = request.get("alert_message")
    data = request.get("data")
    
    success = email_manager.send_alert(to_email, alert_title, alert_message, data)
    return {
        "success": success,
        "message": "Alert sent successfully" if success else "Failed to send alert"
    }
# Settings Endpoints
@app.get("/settings/email")
async def get_email_settings(username: str = Depends(verify_token)):
    """Get email configuration (without password)"""
    email_config = config.get("email")
    # Don't send password to frontend
    safe_config = {
        "enabled": email_config.get("enabled", False),
        "smtp_server": email_config.get("smtp_server", "smtp.gmail.com"),
        "smtp_port": email_config.get("smtp_port", 587),
        "sender_email": email_config.get("sender_email", "")
    }
    return safe_config

@app.post("/settings/email")
async def update_email_settings(
    request: dict,
    username: str = Depends(verify_token)
):
    """Update email configuration"""
    try:
        # Load current config
        current_config = config.config
        
        # Update email settings
        if "email" not in current_config:
            current_config["email"] = {}
        
        current_config["email"]["enabled"] = request.get("enabled", False)
        current_config["email"]["smtp_server"] = request.get("smtp_server", "smtp.gmail.com")
        current_config["email"]["smtp_port"] = request.get("smtp_port", 587)
        current_config["email"]["sender_email"] = request.get("sender_email", "")
        
        # Only update password if provided
        if request.get("sender_password"):
            current_config["email"]["sender_password"] = request["sender_password"]
        
        # Save config
        config.save_config(current_config)
        
        # IMPORTANT: Reload config from file
        config.config = config.load_config()
        
        # Reload email manager with new settings
        from email_manager import email_manager
        email_manager.__init__()
        
        return {"success": True, "message": "Email settings updated"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Email Recipients Storage (in-memory for now)
email_recipients = []

@app.get("/settings/recipients")
async def get_recipients(username: str = Depends(verify_token)):
    """Get list of email recipients"""
    return email_recipients

@app.post("/settings/recipients")
async def add_recipient(request: dict, username: str = Depends(verify_token)):
    """Add email recipient"""
    email = request.get("email", "")
    if email and email not in email_recipients:
        email_recipients.append(email)
    return {"success": True, "message": "Recipient added"}

@app.delete("/settings/recipients/{email}")
async def remove_recipient(email: str, username: str = Depends(verify_token)):
    """Remove email recipient"""
    if email in email_recipients:
        email_recipients.remove(email)
    return {"success": True, "message": "Recipient removed"}  
# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.websocket_endpoint(websocket)

# Main
if __name__ == "__main__":
    print("🚀 Starting AlphaBase v4.0...")
    
    # Start MQTT if enabled
    mqtt_manager.start()
    
    # Get server config
    server_host = config.get("server", "host")
    server_port = config.get("server", "port")
    
    print(f"📡 Server will run on http://{server_host}:{server_port}")
    uvicorn.run(app, host=server_host, port=server_port)