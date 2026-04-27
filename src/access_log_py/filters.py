from dataclasses import dataclass
from typing import List, Optional

from flask import request


@dataclass(frozen=True)
class SkipRule:
    """A rule that, when matched against the current request, suppresses the
    access log record.

    Both fields are AND-combined. A field set to None is ignored.
    """

    path: Optional[str] = None
    user_agent_prefix: Optional[str] = None

    def matches(self) -> bool:
        if self.path is not None and request.path != self.path:
            return False
        if self.user_agent_prefix is not None:
            ua = request.user_agent.string or ""
            if not ua.startswith(self.user_agent_prefix):
                return False
        # If both fields are None the rule would match everything; refuse to
        # silently swallow all traffic.
        if self.path is None and self.user_agent_prefix is None:
            return False
        return True


def default_skip_rules() -> List[SkipRule]:
    """Default rules — drop K8s liveness/readiness probes hitting `/` with a
    `kube-probe/<version>` User-Agent. Override by passing your own list to
    `install(skip_rules=[...])`.
    """
    return [SkipRule(path="/", user_agent_prefix="kube-probe/")]
