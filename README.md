# ClusterFlow
Distributed Multi-Node Backend Architecture using FastAPI, NGINX, and MongoDB
# Distributed Architecture

## Architecture Overview

```
                          Nginx (Load Balancer)
                               |
                          192.168.0.179:80
                               |
                _________________|_______________
               |                                 |
          FastAPI 1                         FastAPI 2
      192.168.0.120:8000              192.168.0.11:8001
               |                                 |
               |_______________|_________________|
                               |
                          MongoDB
                    192.168.0.179:27017
                    Database: "ems"
                    Collection: "meters"
```

## Components

### 1. **Nginx (Reverse Proxy & Load Balancer)**
- **Host**: 192.168.0.179 (Windows Machine)
- **Port**: 80
- **Role**: Routes incoming HTTP requests to FastAPI instances
- **Configuration**: `C:\nginx-1.29.3\conf\nginx.conf`
- **Status**: Running

### 2. **FastAPI Backend Servers**
- **FastAPI 1**: 192.168.0.120:8000
- **FastAPI 2**: 192.168.0.11:8001
- **Role**: Process meter data, handle API requests
- **Database Connection**: MongoDB at 192.168.0.179:27017

### 3. **MongoDB**
- **Host**: 192.168.0.179
- **Port**: 27017
- **Database**: `ems`
- **Collection**: `meters`
- **Role**: Stores meter data (voltage, current, power, frequency, etc.)

---

## API Endpoints

### Home Route
```
GET /
Response: {"server": "hostname", "message": "EMS Backend Running"}
```

### Insert Meter Data
```
POST /meters
Body: {
    "meter_id": "M001",
    "plant": "Plant A",
    "voltage": 230.5,
    "current": 15.2,
    "power": 3500.5,
    "frequency": 50.0,
    "power_factor": 0.95,
    "timestamp": "2026-05-15T14:30:00"
}
Response: {"status": "saved", "meter_id": "M001", "server": "hostname"}
```

### Get All Meter Data
```
GET /meters
Response: [list of all meter records]
```

### Get Data by Meter ID
```
GET /meters/{meter_id}
Example: GET /meters/M001
Response: [list of records for M001]
```

### Get Latest Data for Meter
```
GET /latest/{meter_id}
Example: GET /latest/M001
Response: {latest meter record}
```

### WebSocket (Real-time Data Stream)
```
WebSocket /ws
Continuously sends latest meter data every second
```

---

## Access URLs

### From Local Machine
```
http://localhost/
http://192.168.0.179/
```

### From Another Device on Same LAN
```
http://192.168.0.179/
```

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB running at 192.168.0.179:27017
- Nginx running at 192.168.0.179:80

### 1. Install Python Dependencies

```powershell
cd C:\Users\Admin\Desktop\testing
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Install Required Packages

```powershell
pip install fastapi uvicorn motor pydantic
```

### 3. Run FastAPI Server (on each backend machine)

**On 192.168.0.120:**
```powershell
cd C:\Users\Admin\Desktop\testing
python main.py
```
Server starts at: `http://192.168.0.120:8000`

**On 192.168.0.11:**
```powershell
cd C:\Users\Admin\Desktop\testing
python main.py
```
Server starts at: `http://192.168.0.11:8001`

### 4. Verify MongoDB Connection

```powershell
# Test connection to MongoDB
mongosh --host 192.168.0.179 --port 27017
```

### 5. Start Nginx

```powershell
cd C:\nginx-1.29.3
.\nginx.exe
```

---

## Nginx Configuration

Located at: `C:\nginx-1.29.3\conf\nginx.conf`

**Key Settings:**
- Upstream cluster with two FastAPI servers
- Load balancing (round-robin by default)
- Keepalive connections: 16
- Timeout settings:
  - Connect: 3s
  - Read: 10s
  - Send: 10s
- Failover: If one server fails (5xx errors, timeout), request is sent to next upstream

---

## Testing

### 1. Test Nginx Proxy
```powershell
curl http://192.168.0.179/
```

### 2. Test Direct FastAPI
```powershell
curl http://192.168.0.120:8000/
curl http://192.168.0.11:8001/
```

### 3. Insert Test Data
```powershell
$body = @{
    meter_id = "M001"
    plant = "Plant A"
    voltage = 230.5
    current = 15.2
    power = 3500.5
    frequency = 50.0
    power_factor = 0.95
    timestamp = Get-Date -Format "o"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://192.168.0.179/meters" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### 4. Retrieve Data
```powershell
curl http://192.168.0.179/meters/M001
```

---

## Troubleshooting

### Nginx returns 502 Bad Gateway
- **Cause**: FastAPI servers not reachable
- **Fix**: 
  - Verify FastAPI is running on 192.168.0.120:8000 and 192.168.0.11:8001
  - Check network connectivity: `Test-NetConnection 192.168.0.120 -Port 8000`
  - Restart nginx: `C:\nginx-1.29.3\nginx.exe -s reload`

### MongoDB Connection Error
- **Cause**: MongoDB not running or wrong IP
- **Fix**:
  - Verify MongoDB is running: `mongosh --host 192.168.0.179`
  - Check connection string in `main.py`: `mongodb://192.168.0.179:27017`

### Firewall Blocking Port 80
- **Cause**: Windows Firewall blocking inbound traffic
- **Fix**:
  ```powershell
  New-NetFirewallRule -DisplayName "Allow Nginx Port 80" `
      -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
  ```

### Cannot Access from Remote Device
- **Cause**: Device not on same network or firewall blocks it
- **Fix**:
  - Verify device is on 192.168.0.x network
  - Check Windows Firewall allows port 80
  - Run: `Test-NetConnection 192.168.0.179 -Port 80` from remote device

---

## Performance Notes

- **Load Balancing**: Nginx distributes requests equally between both FastAPI servers
- **Failover**: If one server goes down, traffic is automatically routed to the other
- **Keepalive**: Reduces connection overhead (16 concurrent connections per upstream)
- **MongoDB**: Single instance (consider replica set for production HA)

---

## Production Recommendations

1. **Enable HTTPS**: Add SSL/TLS certificates to Nginx
2. **Health Checks**: Add nginx health check directives
3. **MongoDB**: Deploy as replica set for high availability
4. **Logging**: Enable detailed request logging in Nginx and FastAPI
5. **Monitoring**: Add monitoring for Nginx, FastAPI, and MongoDB
6. **Auto-restart**: Configure Windows Services or use process managers for auto-restart

---

## Files

- **Nginx Config**: `C:\nginx-1.29.3\conf\nginx.conf`
- **FastAPI App**: `C:\Users\Admin\Desktop\testing\main.py`
- **Requirements**: `C:\Users\Admin\Desktop\testing\requirements.txt`
- **MongoDB**: External at `192.168.0.179:27017`

---

## Contact & Support

For issues or questions about this setup, verify:
1. All services are running
2. Network connectivity between components
3. MongoDB is accessible
4. Nginx is not reporting errors in `C:\nginx-1.29.3\logs\error.log`