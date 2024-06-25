from typing import List
from aiogram import types
from aiogram.filters import Filter


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: List[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class GroupIdFilter(Filter):
    def __init__(self, group_id: List[int]) -> None:
        self.group_id = group_id

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id in self.group_id