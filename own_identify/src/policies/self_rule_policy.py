"""
# 根据场景编写的rule base policy module
"""
import logging
import json
import os
import typing
from typing import Any, List, Text, Optional

import rasa
from rasa.core.domain import Domain, InvalidDomain
from rasa.core.events import ActionExecuted
from rasa.core.policies.policy import Policy
from rasa.core.trackers import DialogueStateTracker
from rasa.core.constants import MAPPING_POLICY_PRIORITY

_logger = logging.getLogger(__name__)


class SelfRulePolicy(Policy):
    """self rule policy class"""
    def __init__(self, priority: int = MAPPING_POLICY_PRIORITY) -> None:
        """Create a new self rule policy."""

        super().__init__(priority=priority)

    def predict_action_probabilities(
            self, tracker: DialogueStateTracker, domain: Domain
    ) -> List[float]:
        """Predicts the assigned action."""

    def persist(self, path: Text) -> None:
        """Only persists the priority."""

        config_file = os.path.join(path, "self_rule_policy.json")
        meta = {"priority": self.priority}
        rasa.utils.io.create_directory_for_file(config_file)
        rasa.utils.io.dump_obj_as_json_to_file(config_file, meta)

    @classmethod
    def load(cls, path: Text) -> "SelfRulePolicy":
        """Returns the class with the configured priority."""

        meta = {}
        if os.path.exists(path):
            meta_path = os.path.join(path, "self_rule_policy.json")
            if os.path.isfile(meta_path):
                meta = json.loads(rasa.utils.io.read_file(meta_path))

        return cls(**meta)
