"""Original synthetic demo: guarded agent actions, no network or real customer data."""
import hashlib
import json
import sqlite3


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class TemporaryFailure(Exception):
    pass


class FakeProvider:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = 0
        self.effects = {}

    def execute(self, key, payload):
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise TemporaryFailure("simulated 503")
        if key not in self.effects:
            self.effects[key] = "synthetic-receipt-" + digest({"key": key, "payload": payload})[:12]
        return self.effects[key]


class Guard:
    def __init__(self, file):
        self.db = sqlite3.connect(str(file))
        self.db.execute("""CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY, operation TEXT NOT NULL, payload TEXT NOT NULL,
            hash TEXT NOT NULL, approved INT DEFAULT 0, status TEXT DEFAULT 'pending',
            attempts INT DEFAULT 0, receipt TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS audit(
            seq INTEGER PRIMARY KEY, job_id TEXT, event TEXT, details TEXT DEFAULT '')""")
        self.db.commit()

    def log(self, key, event, details=""):
        self.db.execute("INSERT INTO audit(job_id,event,details) VALUES(?,?,?)", (key,event,details))

    def propose(self, key, operation, payload):
        if not key or not operation or not isinstance(payload, dict):
            raise ValueError("Valid key, operation, and dictionary payload required")
        raw = json.dumps(payload,sort_keys=True)
        hashval = digest(payload)
        existing = self.db.execute("SELECT operation,hash FROM jobs WHERE id=?", (key,)).fetchone()
        if existing:
            if existing != (operation,hashval):
                raise ValueError("Same key with changed payload or operation")
            return self.status(key)
        self.db.execute("INSERT INTO jobs(id,operation,payload,hash) VALUES(?,?,?,?)",
                        (key,operation,raw,hashval))
        self.log(key,"proposed")
        self.db.commit()
        return self.status(key)

    def status(self,key):
        row=self.db.execute("SELECT approved,status,attempts,receipt FROM jobs WHERE id=?",(key,)).fetchone()
        if row is None:
            raise KeyError(key)
        return {"approved":bool(row[0]),"state":row[1],"attempts":row[2],"receipt":row[3]}

    def approve(self,key):
        self.status(key)
        self.db.execute("UPDATE jobs SET approved=1,status='approved' WHERE id=?",(key,))
        self.log(key,"human_approved")
        self.db.commit()

    def execute(self,key,provider,max_attempts=3):
        state=self.status(key)
        if state["state"]=="completed":
            return {**state,"replay_suppressed":True}
        if not state["approved"]:
            return {**state,"blocked":"approval_required"}
        if max_attempts<1:
            raise ValueError("max_attempts")
        payload=json.loads(self.db.execute("SELECT payload FROM jobs WHERE id=?",(key,)).fetchone()[0])
        for _ in range(max_attempts):
            self.db.execute("UPDATE jobs SET status='running',attempts=attempts+1 WHERE id=?",(key,))
            self.log(key,"attempt")
            self.db.commit()
            try:
                receipt=provider.execute(key,payload)
            except TemporaryFailure as exc:
                self.log(key,"transient_failure",str(exc))
                self.db.commit()
                continue
            self.db.execute("UPDATE jobs SET status='completed',receipt=? WHERE id=?",(receipt,key))
            self.log(key,"provider_receipt",receipt)
            self.db.commit()
            return {**self.status(key),"replay_suppressed":False}
        self.db.execute("UPDATE jobs SET status='retry_exhausted' WHERE id=?",(key,))
        self.log(key,"retry_exhausted")
        self.db.commit()
        return self.status(key)

    def events(self,key):
        rows=self.db.execute("SELECT seq,event,details FROM audit WHERE job_id=? ORDER BY seq",(key,)).fetchall()
        return [{"sequence":s,"event":e,"details":d} for s,e,d in rows]

    def close(self):
        self.db.close()
