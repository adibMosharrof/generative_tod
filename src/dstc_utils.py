import glob
import re
from pathlib import Path
from typing import List, Optional, Union
from transformers import AutoTokenizer, PreTrainedTokenizerFast

from tokenizers.processors import TemplateProcessing

from my_enums import SimpleTodConstants, SpecialTokens


def get_dstc_service_name(service_name: str) -> str:
    return service_name[: service_name.find("_")]


def get_dialog_file_paths(data_root, step):
    pattern = "dialogues_*"
    file_paths = glob.glob(str(data_root / step / pattern))
    return file_paths


def get_csv_data_path(
    step: str = "train",
    num_dialogs: int = 1,
    cfg=None,
):
    step_dir = cfg.processed_data_root / step
    return (
        step_dir
        / f"multi_task_{cfg.is_multi_task}_schema_{cfg.should_add_schema}_user_actions_{cfg.should_add_user_actions}_sys_actions_{cfg.should_add_sys_actions}_turns_{cfg.num_turns}_dialogs_{num_dialogs}{SimpleTodConstants.DELEXICALIZED if cfg.delexicalize else ''}_{'_'.join(cfg.domains)}.csv"
    )


def get_tokenizer(model_name: str = "gpt2") -> PreTrainedTokenizerFast:
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        truncation_side="left",
        pad_token=SpecialTokens.pad_token.value,
        bos_token=SpecialTokens.bos_token.value,
        eos_token=SpecialTokens.eos_token.value,
        additional_special_tokens=SpecialTokens.list(),
    )
    tokenizer._tokenizer.post_processor = TemplateProcessing(
        single=f"{tokenizer.bos_token}:0 $A:0 {tokenizer.eos_token}:0",
        special_tokens=[
            (tokenizer.bos_token, tokenizer.bos_token_id),
            (tokenizer.eos_token, tokenizer.eos_token_id),
        ],
    )
    return tokenizer


def get_token_id(tokenizer: AutoTokenizer, token_str: str) -> int:
    return tokenizer(token_str)["input_ids"][0]


def get_text_in_between(
    text: str,
    start_token: str,
    end_token: str,
    default_value: any = None,
    multiple_values: bool = False,
) -> Union[str, list[str]]:
    if not multiple_values:
        try:
            idx1 = text.index(start_token)
            idx2 = text.index(end_token)
            res = text[idx1 + len(start_token) : idx2]
            return res
        except ValueError:
            return default_value
    try:
        if SimpleTodConstants.NEW_LINES in text:
            text = text.replace(SimpleTodConstants.NEW_LINES, "")
        items = re.findall(f"{re.escape(start_token)}(.+?){re.escape(end_token)}", text)
        if not items:
            return default_value
        return items
    except ValueError:
        return default_value

def remove_tokens_from_text(text: str, tokens: List[str]) -> str:
    for token in tokens:
        text = text.replace(token, "")
    return text
