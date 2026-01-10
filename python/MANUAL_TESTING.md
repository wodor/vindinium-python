# Manual Testing Guide: Running Client Against Server

## Overview

This guide documents the process and lessons learned from manually testing the game client against the Python server, particularly for US4 (Legacy Client Integration).

## Prerequisites

- Python 3.11+ with dependencies installed
- MongoDB running (via Docker)
- Node.js for building the client
- Docker/Podman for containerized MongoDB

## Quick Start (The Working Process)

### 1. Start MongoDB

```bash
cd python
docker compose -f docker-compose.test.yml up -d
```

**Wait for MongoDB to be ready:**
```bash
# Check health status
docker ps | grep vindinium-test-mongodb
# Should show "(healthy)" in the status
```

### 2. Ensure Environment Configuration

```bash
cd python
cp .env.example .env
# .env should have:
# MONGODB_URI=mongodb://localhost:27017
# PORT=9000
```

### 3. Start the Game Server (RECOMMENDED METHOD)

**Use uvicorn directly in detached mode:**
```bash
cd python
nohup uvicorn main:app --host localhost --port 9000 > /tmp/server.log 2>&1 &
echo $! > /tmp/server.pid
```

**Why this works better than `python main.py`:**
- More control over process lifecycle
- Easier to monitor with logs
- Clean shutdown possible
- Process ID saved for later cleanup

### 4. Verify Server is Running

```bash
# Check if server is up
curl http://localhost:9000/health

# Check process
cat /tmp/server.pid | xargs ps -p

# View logs
tail -f /tmp/server.log
```

### 5. Build the Client (One-time)

```bash
cd client
npm install
NODE_ENV=production npx grunt build
```

**Output locations:**
- `public/bundle.js` (1.3MB)
- `public/bundle.css` (4.4KB)

### 6. Test the Integration

**Create a game:**
```bash
GAME_ID=$(curl -s -X POST http://localhost:9000/api/training \
  -d "key=test&turns=50" | \
  python -c "import json,sys; print(json.load(sys.stdin)['game']['id'])")
echo "Game ID: $GAME_ID"
```

**View in browser:**
```
http://localhost:9000/$GAME_ID
```

**Test SSE streaming:**
```bash
# Should stream game states (press Ctrl+C to stop)
curl http://localhost:9000/events/$GAME_ID
```

### 7. Cleanup

```bash
# Stop server
cat /tmp/server.pid | xargs kill
rm /tmp/server.pid

# Stop MongoDB
cd python
docker compose -f docker-compose.test.yml down -v
```

---

## Common Issues & Solutions

### Issue 1: Port Already in Use

**Symptom:**
```
ERROR: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process on port 9000
lsof -i :9000

# Kill specific PIDs (NOT pkill - not allowed in CI)
kill <PID1> <PID2>

# Wait and verify
sleep 2
lsof -i :9000  # Should return empty
```

**Why this happens:**
- Previous server didn't shut down cleanly
- Background processes still holding port
- Using `python main.py &` without proper process management

### Issue 2: Server Exits Immediately

**Symptom:**
```bash
python main.py &
# Process exits right away
```

**Root cause:**
- Background process without proper daemon setup
- No output redirection causes issues
- Process lifecycle not managed

**Solution:**
Use uvicorn directly with nohup (see Quick Start #3)

### Issue 3: CSS/JS Files Not Found (404)

**Symptom:**
Browser console shows 404 for `/assets/css/vindinium.css`

**Solution:**
```bash
# Ensure CSS file exists
ls -la public/css/vindinium.css

# If missing, create from style.css
cp public/css/style.css public/css/vindinium.css

# Verify static mounting in main.py
grep -A 3 "StaticFiles" python/main.py
```

### Issue 4: MongoDB Not Ready

**Symptom:**
Server starts but database operations fail

**Solution:**
```bash
# Wait for healthy status before starting server
timeout 30 bash -c 'until docker exec vindinium-test-mongodb \
  mongosh --eval "db.adminCommand(\"ping\")" > /dev/null 2>&1; \
  do sleep 1; done'
echo "MongoDB is ready"
```

### Issue 5: Can't Kill Process (pkill forbidden)

**Symptom:**
```
Command not executed. The 'pkill' command is not allowed.
```

**Solution:**
```bash
# WRONG: pkill -f "python main.py"

# CORRECT: Use specific PID
ps aux | grep uvicorn | grep -v grep | awk '{print $2}'
kill <PID>

# Or use saved PID file
cat /tmp/server.pid | xargs kill
```

---

## Process Management Best Practices

### DO ✅

1. **Use uvicorn directly:**
   ```bash
   nohup uvicorn main:app --host localhost --port 9000 > /tmp/server.log 2>&1 &
   ```

2. **Save process ID:**
   ```bash
   echo $! > /tmp/server.pid
   ```

3. **Redirect output:**
   ```bash
   > /tmp/server.log 2>&1
   ```

4. **Check health before testing:**
   ```bash
   curl http://localhost:9000/health
   ```

5. **Use specific PIDs for kill:**
   ```bash
   kill $(cat /tmp/server.pid)
   ```

### DON'T ❌

1. **Don't use `python main.py &` directly**
   - No log redirection
   - Hard to track process
   - May exit unexpectedly

2. **Don't use pkill/killall**
   - Not allowed in CI environments
   - Too broad, may kill wrong processes

3. **Don't skip MongoDB health check**
   - Leads to database connection errors
   - Hard to debug

4. **Don't start server before MongoDB is ready**
   - Connection errors
   - Failed initializations

---

## Automated vs Manual Testing

### GitHub Actions Workflow (`.github/workflows/copilot-setup-steps.yml`)

**Current workflow is OPTIMAL for CI ✅**

**Strengths:**
- ✅ Proper health check for MongoDB (30s timeout)
- ✅ Uses E2E test suite (automatic server management)
- ✅ Cleanup always runs (`if: always()`)
- ✅ Timeout protection (5 minutes)
- ✅ Uses `docker compose` correctly

**Why it works well:**
```yaml
- name: Start MongoDB container
  run: |
    cd python
    docker compose -f docker-compose.test.yml up -d
    # Wait for MongoDB to be ready
    timeout 30 bash -c 'until docker exec vindinium-test-mongodb \
      mongosh --eval "db.adminCommand(\"ping\")" > /dev/null 2>&1; \
      do sleep 1; done'
    echo "MongoDB is ready"

- name: Run E2E tests
  run: |
    cd python
    python run_e2e_tests.py -v
  timeout-minutes: 5
```

**The E2E test runner manages:**
- Server startup (uvicorn subprocess)
- Test execution
- Server shutdown
- Error handling

**No changes needed for CI workflow!**

### Manual Testing Differences

**Manual testing requires:**
- Process management (save PIDs)
- Log file redirection
- Explicit cleanup steps
- Browser-based verification

**CI/automated testing handles:**
- Everything automatically via `run_e2e_tests.py`
- Subprocess management
- Cleanup in finally blocks

---

## Debugging Tips

### View Server Logs

```bash
# Real-time
tail -f /tmp/server.log

# Search for errors
grep ERROR /tmp/server.log

# Last 50 lines
tail -50 /tmp/server.log
```

### Check MongoDB Logs

```bash
docker logs vindinium-test-mongodb

# Follow logs
docker logs -f vindinium-test-mongodb
```

### Verify Port Binding

```bash
# Check what's listening on port 9000
lsof -i :9000

# Alternative
ss -tlnp | grep 9000
netstat -tlnp | grep 9000
```

### Test SSE Streaming

```bash
# Should see JSON game states
timeout 5 curl -s http://localhost:9000/events/$GAME_ID | head -20
```

### Verify Static Files

```bash
# Check if served correctly
curl -I http://localhost:9000/assets/js/bundle.js
# Should return 200 OK with correct content-type
```

---

## Environment Differences

### Local Development
- Manual process management needed
- Browser testing available
- Log files for debugging
- Can keep server running between tests

### CI/GitHub Actions
- Automated via run_e2e_tests.py
- No browser, only API testing
- Process cleanup in try/finally
- Fresh environment each run

### Copilot Agent Environment
- Limited to command-line tools
- No browser UI (use playwright for screenshots)
- Process management restrictions (no pkill)
- Need explicit PID tracking

---

## Testing Checklist

Before claiming "client integration works":

- [ ] MongoDB container running and healthy
- [ ] Server starts without errors
- [ ] Health endpoint responds: `curl http://localhost:9000/health`
- [ ] Training game creation works: `POST /api/training`
- [ ] Static assets served: `/assets/js/bundle.js` returns 200
- [ ] Game viewer HTML loads: `GET /{game_id}`
- [ ] SSE stream works: `GET /events/{game_id}` 
- [ ] Browser renders game board (if browser available)
- [ ] TV mode works: `GET /tv`
- [ ] Now-playing stream works: `GET /now-playing`
- [ ] Server logs show no errors
- [ ] Cleanup successful (port 9000 freed, MongoDB stopped)

---

## Summary: The Learned Process

### For Manual Testing (like US4 implementation)

1. Start MongoDB with health check
2. Use uvicorn with nohup and log redirection
3. Save PID to file for cleanup
4. Verify server health before testing
5. Test endpoints with curl first
6. Use playwright for visual verification
7. Clean up with specific PIDs

### For Automated Testing (CI)

The existing workflow is optimal - use `run_e2e_tests.py` which handles everything.

### Key Insight

**Manual testing complexity ≠ CI workflow problem**

The challenges (port conflicts, process management) are specific to **interactive development** and don't indicate issues with the CI workflow. The CI workflow correctly delegates to `run_e2e_tests.py` which has proper subprocess management.

**No changes needed to `.github/workflows/copilot-setup-steps.yml`** ✅

---

## Future Improvements (Optional)

### For Manual Testing Convenience

Could create a helper script:

```bash
# python/start_dev_server.sh
#!/bin/bash
cd "$(dirname "$0")"

# Start MongoDB
docker compose -f docker-compose.test.yml up -d
timeout 30 bash -c 'until docker exec vindinium-test-mongodb mongosh --eval "db.adminCommand(\"ping\")" > /dev/null 2>&1; do sleep 1; done'

# Start server
nohup uvicorn main:app --host localhost --port 9000 > /tmp/server.log 2>&1 &
echo $! > /tmp/server.pid

echo "Server started (PID: $(cat /tmp/server.pid))"
echo "View logs: tail -f /tmp/server.log"
echo "Health: curl http://localhost:9000/health"
```

```bash
# python/stop_dev_server.sh
#!/bin/bash
cd "$(dirname "$0")"

if [ -f /tmp/server.pid ]; then
  kill $(cat /tmp/server.pid)
  rm /tmp/server.pid
  echo "Server stopped"
fi

docker compose -f docker-compose.test.yml down -v
echo "MongoDB stopped"
```

But these are convenience only - **not required for CI or production.**
