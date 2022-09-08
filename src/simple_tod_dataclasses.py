from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import zip_longest
from typing import Dict, List, Optional, Union

import torch


@dataclass
class SimpleTodBelief:
    domain: str
    slot_name: str
    value: any
    prediction: Optional[str] = ""

    @classmethod
    def from_string(self, text: str):
        try:
            dom_slot, value = text.split(SimpleTodConstants.SLOT_VALUE_SEPARATOR)
        except ValueError:
            return self("", "", "", text)
        try:
            domain, slot_name = dom_slot.split(SimpleTodConstants.DOMAIN_SLOT_SEPARATOR)
        except ValueError:
            return self("", "", value, text)
        return self(domain, slot_name, value)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "".join(
            [
                self.domain,
                SimpleTodConstants.DOMAIN_SLOT_SEPARATOR,
                self.slot_name,
                SimpleTodConstants.SLOT_VALUE_SEPARATOR,
                self.value,
            ]
        )


@dataclass
class SimpleTodAction:
    domain: str
    action_type: str
    slot_name: Optional[str] = ""
    values: Optional[str] = ""
    prediction: Optional[str] = ""

    @classmethod
    def from_string(self, text: str):
        try:
            action_type, rest = text.split(SimpleTodConstants.SLOT_VALUE_SEPARATOR)
        except ValueError:
            return self("", "", prediction=text)
        try:
            dom_slot, values = rest.split(SimpleTodConstants.ACTION_VALUE_SEPARATOR)
        except ValueError:
            return self("", action_type, prediction=text)
        try:
            domain, slot_name = dom_slot.split(SimpleTodConstants.DOMAIN_SLOT_SEPARATOR)
        except ValueError:
            return self("", action_type, values, text)
        return self(domain, action_type, slot_name, values)

    def __eq__(self, other) -> bool:
        return (
            self.domain == other.domain
            and self.action_type == other.action_type
            and self.slot_name == other.slot_name
            and self.values == other.values
        )

    def is_inform(self) -> bool:
        return (
            self.action_type == SimpleTodConstants.ACTION_TYPE_INFORM
            or self.action_type == SimpleTodConstants.ACTION_TYPE_INFORM_COUNT
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "".join(
            [
                self.action_type,
                SimpleTodConstants.SLOT_VALUE_SEPARATOR,
                self.domain,
                SimpleTodConstants.DOMAIN_SLOT_SEPARATOR,
                self.slot_name,
                SimpleTodConstants.ACTION_VALUE_SEPARATOR,
                self.values,
            ]
        )


@dataclass
class SimpleTodRequestedSlot:
    domain: str
    slot_name: str

    @classmethod
    def from_string(self, text: str):
        try:
            domain, slot_name = text.split(SimpleTodConstants.DOMAIN_SLOT_SEPARATOR)
        except ValueError:
            return self("", text)
        return self(domain, slot_name)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self.domain == other.domain and self.slot_name == other.slot_name

    def __str__(self) -> str:
        return "".join(
            [
                self.domain,
                SimpleTodConstants.DOMAIN_SLOT_SEPARATOR,
                self.slot_name,
            ]
        )


@dataclass
class SimpleTodContext:
    user_utterances: deque[str] = field(default_factory=deque)
    system_utterances: deque[str] = field(default_factory=deque)
    next_system_utterance: str = None
    current_user_utterance: str = None

    def __init__(self, max_length: int = 10):
        self.user_utterances = deque(maxlen=max_length)
        self.system_utterances = deque(maxlen=max_length)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        out = SpecialTokens.begin_context
        for user, system in zip_longest(
            self.user_utterances, self.system_utterances, fillvalue=""
        ):
            if user:
                out += SpecialTokens.user + user
            if system:
                out += SpecialTokens.system + system

        out += (
            SpecialTokens.begin_last_user_utterance
            + self.current_user_utterance
            + SpecialTokens.end_last_user_utterance
        )
        return out


@dataclass
class SimpleTodTarget:
    beliefs: List[SimpleTodBelief]
    actions: List[SimpleTodAction]
    response: str
    active_intent: Optional[str] = None
    requested_slots: Optional[List[SimpleTodRequestedSlot]] = None

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        out = SpecialTokens.begin_target

        if self.active_intent:
            out += SpecialTokens.begin_intent
            out += self.active_intent
            out += SpecialTokens.end_intent + SimpleTodConstants.NEW_LINES

        if self.requested_slots:
            out += SpecialTokens.begin_requested_slots
            out += SimpleTodConstants.ITEM_SEPARATOR.join(
                map(str, self.requested_slots)
            )
            out += SpecialTokens.end_requested_slots + SimpleTodConstants.NEW_LINES

        out += SpecialTokens.begin_belief
        out += SimpleTodConstants.ITEM_SEPARATOR.join(map(str, self.beliefs))
        out += SpecialTokens.end_belief + SimpleTodConstants.NEW_LINES

        out += SpecialTokens.begin_action
        out += SimpleTodConstants.ITEM_SEPARATOR.join(map(str, self.actions))
        out += SpecialTokens.end_action + SimpleTodConstants.NEW_LINES

        out += SpecialTokens.begin_response
        out += self.response
        out += SpecialTokens.end_response + SimpleTodConstants.NEW_LINES

        # out += SpecialTokens.end_of_text
        return out


@dataclass
class SimpleTodTurnCsvRow:
    dialog_id: str
    turn_id: str
    context: str
    target: str


@dataclass
class SimpleTodTurn:
    context: SimpleTodContext
    target: SimpleTodTarget
    dialog_id: Optional[str] = None
    turn_id: Optional[int] = None

    def to_csv_row(self) -> List[any]:
        return [self.dialog_id, self.turn_id, str(self.context), str(self.target)]


class Speaker(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"


class SpecialTokens(str, Enum):
    begin_target = "<|begintarget|>"
    end_target = "<|endtarget|>"

    begin_context = "<|begincontext|>"
    end_context = "<|endcontext|>"
    system = "<|system|>"
    user = "<|user|>"
    begin_last_user_utterance = "<|beginlastuserutterance|>"
    end_last_user_utterance = "<|endlastuserutterance|>"

    begin_belief = "<|beginbelief|>"
    end_belief = "<|endbelief|>"

    begin_response = "<|beginresponse|>"
    end_response = "<|endresponse|>"

    begin_action = "<|beginaction|>"
    end_action = "<|endaction|>"

    begin_intent = "<|beginintent|>"
    end_intent = "<|endintent|>"

    begin_requested_slots = "<|beginrequestedslots|>"
    end_requested_slots = "<|endrequestedslots|>"

    prompt_intent = "<|promptintent|>"
    prompt_requested_slots = "<|promptrequestedslots|>"
    prompt_belief = "<|promptbelief|>"
    prompt_action = "<|promptaction|>"
    prompt_response = "<|promptresponse|>"

    @classmethod
    def list(cls):
        return [c.value for c in cls]


class TokenizerTokens(str, Enum):
    pad_token = "<|pad|>"
    eos_token = "<|endoftext|>"
    bos_token = "<|startoftext|>"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()


class SimpleTodConstants(str, Enum):
    DELEXICALIZED = "_delexicalized"
    SLOT_VALUE_SEPARATOR = "->"
    DOMAIN_SLOT_SEPARATOR = "_"
    ITEM_SEPARATOR = "|"
    ACTION_VALUE_SEPARATOR = "<-"
    NEW_LINES = "\n\n"
    ACTION_TYPE_INFORM = "INFORM"
    ACTION_TYPE_INFORM_COUNT = "INFORM_COUNT"


class GoalMetricConfigType(str, Enum):
    ACTION = "action"
    BELIEF = "belief"

    def __repr__(self) -> str:
        return self.value


class SpecialPredictions(str, Enum):
    DUMMY = "DUMMY"


# Datamodule classes
@dataclass
class SimpleTodDatasetItem:
    context: str
    target: str


@dataclass
class SimpleTodTestDataRow:
    context_tokens: torch.Tensor
    context_attention_masks: torch.Tensor
    label_tokens: torch.Tensor
    label_attention_masks: torch.Tensor
    contexts_text: str
    targets_text: str


@dataclass
class SimpleTodTestDataBatch:
    context_tokens: torch.Tensor
    context_attention_masks: torch.Tensor
    label_tokens: torch.Tensor
    label_attention_masks: torch.Tensor
    contexts_text: List[str]
    targets_text: List[str]

    def __iter__(self):
        for item in zip(
            self.context_tokens,
            self.context_attention_masks,
            self.label_tokens,
            self.label_attention_masks,
            self.contexts_text,
            self.targets_text,
        ):
            yield SimpleTodTestDataRow(*item)


@dataclass
class MultiTaskSpecialTokens:
    start_token: SpecialTokens
    end_token: SpecialTokens
    prompt_token: SpecialTokens


def get_multi_task_special_tokens() -> list[MultiTaskSpecialTokens]:
    return [
        MultiTaskSpecialTokens(
            SpecialTokens.begin_intent,
            SpecialTokens.end_intent,
            SpecialTokens.prompt_intent,
        ),
        MultiTaskSpecialTokens(
            SpecialTokens.begin_requested_slots,
            SpecialTokens.end_requested_slots,
            SpecialTokens.prompt_requested_slots,
        ),
        MultiTaskSpecialTokens(
            SpecialTokens.begin_belief,
            SpecialTokens.end_belief,
            SpecialTokens.prompt_belief,
        ),
        MultiTaskSpecialTokens(
            SpecialTokens.begin_action,
            SpecialTokens.end_action,
            SpecialTokens.prompt_action,
        ),
        MultiTaskSpecialTokens(
            SpecialTokens.begin_response,
            SpecialTokens.end_response,
            SpecialTokens.prompt_response,
        ),
    ]
