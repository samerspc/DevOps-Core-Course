# Lab 18 — local IPFS (Task 1)

## Start Kubo

```bash
cd labs/lab18
docker compose up -d
docker compose logs -f ipfs   # optional; Ctrl+C to exit
```

- **Web UI:** http://127.0.0.1:5001/webui  
- **HTTP gateway:** http://127.0.0.1:8080  

## Add content and read via gateway

```bash
# Add the sample file (CID printed on stdout)
docker exec ipfs-lab18 ipfs add -Q /labwork/hello-ipfs.txt

# Or add the course landing page (larger object)
docker exec ipfs-lab18 ipfs add -Q /labwork/index.html
```

Copy the returned **CID** (starts with `Qm…` or `bafy…`), then:

```bash
CID=<paste-cid-here>
curl -sI "http://127.0.0.1:8080/ipfs/${CID}" | head -5
```

**Pin** (keep after GC):

```bash
docker exec ipfs-lab18 ipfs pin add <CID>
docker exec ipfs-lab18 ipfs pin ls | head
```

## Stop / reset

```bash
docker compose down          # keeps volume
docker compose down -v       # wipes local IPFS repo (destructive)
```

For **4EVERLAND** hosting (Tasks 2–6), follow the root **`4EVERLAND.md`** runbook.
