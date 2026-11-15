"""Run the synthetic demo and write a reproducible trace with no secrets."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from guard import Guard,FakeProvider


def demo():
    with TemporaryDirectory(prefix="synthetic_guard_") as tmp:
        db=Path(tmp)/"actions.sqlite"
        provider=FakeProvider(failures=1)
        engine=Guard(db)
        key="demo-0001"
        engine.propose(key,"fake_crm_update",{"customer":"Example Company","case":"SYN-42"})
        blocked=engine.execute(key,provider)
        assert blocked["blocked"]=="approval_required" and provider.calls==0
        engine.approve(key)
        result=engine.execute(key,provider)
        assert result["state"]=="completed" and result["attempts"]==2
        assert engine.execute(key,provider)["replay_suppressed"]
        trace=engine.events(key)
        engine.close()
        engine=Guard(db)
        assert engine.execute(key,provider)["replay_suppressed"]
        assert provider.calls==2 and len(provider.effects)==1
        engine.close()
    data={
        "synthetic_only":True,
        "approved_before_execution":True,
        "injected_failure":"simulated 503, first attempt",
        "outcome":result,
        "restart_replay_suppressed":True,
        "provider_call_count":provider.calls,
        "provider_side_effect_count":len(provider.effects),
        "audit_trace":trace,
        "limitation":"Exactly-once effects require real provider idempotency or reconciliation."
    }
    output=Path(__file__).with_name("sample_trace.json")
    output.write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(json.dumps({"PASS":True,"trace":str(output),"provider_calls":provider.calls,
                      "effects":len(provider.effects),"audit_events":len(trace)},indent=2))


if __name__=="__main__":
    demo()
