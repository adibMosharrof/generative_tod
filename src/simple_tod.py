from pathlib import Path
import hydra
from omegaconf import DictConfig, OmegaConf
import glob
from tqdm import tqdm
import utils
from my_dataclasses import (
    DstcFrame,
    Speaker,
    TodAction,
    TodBelief,
    TodTarget,
    TodTurn,
    TodContext,
    DstcDialog,
    DstcTurn,
)
import copy
import json
import numpy as np
from typing import List


class SimpleTODDataPrep:
    def __init__(self, data_root: str, out_root: str):
        self.data_root = Path(data_root)
        self.out_root = self.data_root / out_root
        self.out_root.mkdir(parents=True, exist_ok=True)

    def _get_dialog_file_paths(self, step):
        file_paths = glob.glob(str(self.data_root / step / "dialogues_*"))
        return file_paths

    def _prepare_context(
        self, user_turn: DstcTurn, system_turn: DstcTurn, prev_tod_turn: TodTurn
    ):
        a = 1
        if not prev_tod_turn:
            context = TodContext()
        else:
            context = copy.deepcopy(prev_tod_turn.context)
            context.system_utterances.append(
                prev_tod_turn.context.next_system_utterance
            )

        if user_turn:
            context.user_utterances.append(user_turn.utterance)
        if system_turn:
            # context.system_utterances.append(system_turn.utterance)
            context.next_system_utterance = system_turn.utterance
        return context

    def _prepare_belief(self, user_turn: DstcTurn) -> List[TodBelief]:
        beliefs = []
        for frame in user_turn.frames:
            if not frame.state:
                continue
            for slot_name, value in frame.state.slot_values.items():
                beliefs.append(TodBelief(frame.service, slot_name, " ".join(value)))
        return beliefs

    def _create_user_action(self, actions, frames: List[DstcFrame]):
        for frame in frames:
            for action in frame.actions:
                actions.append(
                    TodAction(frame.service, action.act, " ".join(action.values))
                )

    def _create_system_action(self, actions, frames: List[DstcFrame]):
        for frame in frames:
            for action in frame.actions:
                actions.append(TodAction(frame.service, action.act, action.slot))

    def _prepare_action(
        self, user_turn: DstcTurn, system_turn: DstcTurn
    ) -> List[TodAction]:
        actions = []
        # if (
        #     user_turn
        #     and system_turn
        #     and len(user_turn.frames) * len(system_turn.frames) > 1
        # ):
        #     raise ValueError("length of frames is greater than 1")
        if user_turn:
            self._create_user_action(actions, user_turn.frames)
        if system_turn:
            self._create_system_action(actions, system_turn.frames)
        return actions

    def _prepare_response(self, system_turn: DstcTurn) -> str:
        if not system_turn:
            return None
        return system_turn.utterance

    def _prepare_target(
        self,
        user_turn: DstcTurn,
        system_turn: DstcTurn,
    ):
        beliefs = self._prepare_belief(user_turn)
        actions = self._prepare_action(user_turn, system_turn)
        response = self._prepare_response(system_turn)
        return TodTarget(beliefs, actions, response)

    def _prepare_turn(
        self, user_turn: DstcTurn, system_turn: DstcTurn, prev_tod_turn: TodTurn
    ) -> TodTurn:
        target = None
        context = self._prepare_context(user_turn, system_turn, prev_tod_turn)
        target = self._prepare_target(user_turn, system_turn)
        out = str(target)
        return TodTurn(context, target)

    def _prepare_dialog(self, dstc_dialog: DstcDialog):
        tod_turns = []
        tod_turn = None
        for user_turn, system_turn in utils.grouper(dstc_dialog.turns, 2):
            tod_turn = self._prepare_turn(user_turn, system_turn, tod_turn)
            tod_turn.dialog_id = dstc_dialog.dialogue_id
            tod_turns.append(tod_turn)
        return tod_turns

    def _prepare_dialog_file(self, path):
        data = []
        dialog_json_data = utils.read_json(path)
        for d in dialog_json_data:
            dialog = DstcDialog.from_json(json.dumps(d))
            prepped_dialog = self._prepare_dialog(dialog)
            data = np.concatenate([data, prepped_dialog])
        return data

    def run(self):
        steps = ["train", "dev", "test"]
        for step in tqdm(steps):
            step_dir = Path(self.out_root / step)
            step_dir.mkdir(parents=True, exist_ok=True)
            dialog_paths = self._get_dialog_file_paths(step)
            out_data = []
            for dp in dialog_paths:
                dialog_data = self._prepare_dialog_file(dp)
                out_data = np.concatenate([out_data, dialog_data])
        a = 1


@hydra.main(config_path="../config/data_prep/", config_name="simple_tod")
def hydra_start(cfg: DictConfig) -> None:
    stdp = SimpleTODDataPrep(
        cfg.data_root,
        cfg.out_root,
        # cfg.metrics,
        # log_dir=cfg.log_dir,
        # title=cfg.plot_title,
    )
    stdp.run()


if __name__ == "__main__":
    hydra_start()
