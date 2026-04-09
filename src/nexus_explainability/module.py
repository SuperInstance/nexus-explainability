'''Nexus Explainability — decision logging, audit trails, explanation generation.'''
import time, json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Decision:
    decision_id: str; timestamp: float; agent_id: str
    decision_type: str; input_state: Dict; output_action: str
    reasoning: str = ""; confidence: float = 1.0
    alternatives: List[Dict] = field(default_factory=list)
    impact: str = ""; metadata: Dict = field(default_factory=dict)

class AuditTrail:
    def __init__(self, max_entries: int = 10000):
        self.decisions: List[Decision] = []; self.max = max_entries
    def record(self, decision: Decision) -> None:
        self.decisions.append(decision)
        if len(self.decisions) > self.max: self.decisions = self.decisions[-self.max:]
    def query(self, agent_id: str = None, decision_type: str = None,
              since: float = 0) -> List[Decision]:
        results = self.decisions
        if agent_id: results = [d for d in results if d.agent_id == agent_id]
        if decision_type: results = [d for d in results if d.decision_type == decision_type]
        if since: results = [d for d in results if d.timestamp >= since]
        return results
    def explain(self, decision_id: str) -> Dict:
        d = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if not d: return {"error": "not found"}
        chain = [dd for dd in self.decisions if dd.timestamp <= d.timestamp and dd.agent_id == d.agent_id]
        return {"decision": d.decision_id, "reasoning": d.reasoning,
                "confidence": d.confidence, "alternatives": d.alternatives,
                "chain_length": len(chain), "context_chain": chain[-5:]}

class ExplanationGenerator:
    def __init__(self, trail: AuditTrail):
        self.trail = trail
    def natural_language(self, decision_id: str) -> str:
        info = self.trail.explain(decision_id)
        if "error" in info: return "Decision not found."
        d = next((d for d in self.trail.decisions if d.decision_id == decision_id), None)
        if not d: return ""
        parts = [f"Agent {d.agent_id} decided to {d.output_action}."]
        if d.reasoning: parts.append(f"Reasoning: {d.reasoning}")
        parts.append(f"Confidence: {d.confidence:.0%}")
        if d.alternatives: parts.append(f"Alternatives considered: {len(d.alternatives)}")
        return " ".join(parts)
    def confidence_summary(self, agent_id: str, hours: float = 1) -> Dict:
        since = time.time() - hours * 3600
        decisions = self.trail.query(agent_id=agent_id, since=since)
        if not decisions: return {"agent": agent_id, "decisions": 0}
        confs = [d.confidence for d in decisions]
        return {"agent": agent_id, "decisions": len(decisions),
                "avg_confidence": sum(confs)/len(confs), "min_confidence": min(confs)}

def demo():
    print("=== Explainability ===")
    trail = AuditTrail()
    for i in range(5):
        trail.record(Decision(f"dec_{i}", time.time(), "auv_1", "navigation",
            {"depth": 5.0+i}, f"go deeper to {5.0+i}m",
            confidence=0.9-i*0.1, alternatives=[{"action":"surface","conf":0.3+i*0.1}]))
    gen = ExplanationGenerator(trail)
    print(gen.natural_language("dec_2"))
    print(json.dumps(gen.confidence_summary("auv_1"), indent=2))
    recent = trail.query(agent_id="auv_1", since=time.time()-10)
    print(f"Recent decisions: {len(recent)}")

if __name__ == "__main__": demo()
