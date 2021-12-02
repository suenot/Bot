from saya import Vk

import regex

import config
import patterns

from tokens import BOT_TOKEN
from userbot import UserBot
from modules.data_service import BetterBotBaseDataService
from modules.commands import Commands
from typing import NoReturn

CHAT_ID_OFFSET = 2e9


class V(Vk):
    def __init__(self, token, group_id, debug=True):
        Vk.__init__(self, token=token, group_id=group_id, debug=debug)
        self.messages_to_delete = {}
        # self.userbot = UserBot()
        self.data = BetterBotBaseDataService()
        self.commands = Commands(self, self.data)
        self.commands.register_cmds(
            (patterns.HELP, self.commands.help_message),
            (patterns.INFO, self.commands.info_message),
            (patterns.UPDATE, self.commands.update_command),
            (patterns.ADD_PROGRAMMING_LANGUAGE, lambda: self.commands.change_programming_language(True)),
            (patterns.REMOVE_PROGRAMMING_LANGUAGE, lambda: self.commands.change_programming_language(False)),
            (patterns.ADD_GITHUB_PROFILE, lambda: self.commands.change_github_profile(True)),
            (patterns.REMOVE_GITHUB_PROFILE, lambda: self.commands.change_github_profile(False)),
            (patterns.KARMA, self.commands.karma_message),
            (patterns.TOP, self.commands.top),
            (patterns.PEOPLE, self.commands.top),
            (patterns.BOTTOM, lambda: self.commands.top(True)),
            (patterns.TOP_LANGUAGES, self.commands.top_langs),
            (patterns.PEOPLE_LANGUAGES, self.commands.top_langs),
            (patterns.BOTTOM_LANGUAGES, lambda: self.commands.top_langs(True)),
            (patterns.APPLY_KARMA, self.commands.apply_karma),
        )

    def message_new(self, event):
        """
        Handling all new messages.
        """
        event = event["object"]["message"]
        msg = event["text"].lstrip("/")
        peer_id = event["peer_id"]
        from_id = event["from_id"]
        msg_id = event["conversation_message_id"]

        if peer_id in self.messages_to_delete:
            peer = CHAT_ID_OFFSET + config.userbot_chats[peer_id]
            new_messages_to_delete = []
            ids = []

            for item in self.messages_to_delete[peer_id]:
                if item['date'] > datetime.now():
                    new_messages_to_delete.append(item)
                else:
                    ids.append(item['id'])

            if new_messages_to_delete:
                self.messages_to_delete[peer_id] = new_messages_to_delete
            else:
                self.messages_to_delete.pop(peer_id)

            if ids:
                self.userbot.delete_messages(ids, peer)

        user = self.data.get_or_create_user(from_id, self) if from_id > 0 else None

        messages = self.get_messages(event)
        selected_message = messages[0] if len(messages) == 1 else None
        selected_user = self.data.get_or_create_user(selected_message["from_id"], self) if selected_message else None

        self.commands.process(msg, peer_id, from_id, messages, msg_id, user, selected_user)


    def get_users_sorted_by_karma(self, peer_id, reverse_sort=True):
        members = self.get_members_ids(peer_id)
        users = self.data.get_users(other_keys=["karma", "name", "programming_languages", "supporters", "opponents", "github_profile", "uid"],
                                    sort_key=self.calculate_real_karma, reverse_sort=reverse_sort)
        if members:
            users = [u for u in users if u["uid"] in members]
        return users

    def get_users_sorted_by_name(self, peer_id):
        members = self.get_members_ids(peer_id)
        users = self.data.get_users(other_keys=["name", "programming_languages", "github_profile", "uid"])
        if members:
            users = [u for u in users if u["uid"] in members]
        users.reverse()
        return users

    def calculate_real_karma(self, user):
        base_karma = self.data.get_user_property(user, "karma")
        up_votes = len(self.data.get_user_property(user, "supporters"))/config.positive_votes_per_karma
        down_votes = len(self.data.get_user_property(user, "opponents"))/config.negative_votes_per_karma
        return base_karma + up_votes - down_votes


    def delete_message(self, peer_id: int, msg_id: int, delay: int = 2) -> NoReturn:
        if peer_id in config.userbot_chats and peer_id in config.chats_deleting:
            if peer_id not in self.messages_to_delete:
                self.messages_to_delete.update({peer_id: []})
            data = {'date': datetime.now() + timedelta(seconds=delay), 'id': msg_id}
            self.messages_to_delete[peer_id].append(data)

    def get_members(self, peer_id):
        return self.messages.getConversationMembers(peer_id=peer_id)

    def get_members_ids(self, peer_id):
        members = self.get_members(peer_id)
        if "error" in members:
            return
        else:
            return [m["member_id"] for m in members["response"]["items"] if m["member_id"] > 0]

    def send_message(self, event, message):
        self.messages.send(message=message, peer_id=event["peer_id"], disable_mentions=1, random_id=0)

    def send_msg(self, msg: str, peer_id: int) -> NoReturn:
        self.messages.send(message=msg, peer_id=peer_id, disable_mentions=1, random_id=0)

    def get_user_name(self, user_id):
        return self.users.get(user_ids=user_id)['response'][0]["first_name"]


    @staticmethod
    def get_messages(event):
        reply_message = event.get("reply_message", {})
        return [reply_message] if reply_message else event.get("fwd_messages", [])

    @staticmethod
    def get_default_programming_language(language):
        for default_programming_language in config.default_programming_languages:
            default_programming_language = default_programming_language.replace('\\', '')
            if default_programming_language.lower() == language.lower():
                return default_programming_language

    @staticmethod
    def contains_string(strings, matchedString, ignoreCase):
        if ignoreCase:
            for string in strings:
                if string.lower() == matchedString.lower():
                    return True
        else:
            for string in strings:
                if string == matchedString:
                    return True

    @staticmethod
    def contains_all_strings(strings, matchedStrings, ignoreCase):
        matched_strings_count = len(matchedStrings)
        for string in strings:
            if V.contains_string(matchedStrings, string, ignoreCase):
                matched_strings_count -= 1
                if matched_strings_count == 0:
                    return True

    @staticmethod
    def get_karma_hours_limit(karma):
        for limit_item in config.karma_limit_hours:
            if not limit_item["min_karma"] or karma >= limit_item["min_karma"]:
                if not limit_item["max_karma"] or karma < limit_item["max_karma"]:
                    return limit_item["limit"]
        return 168  # hours (a week)


if __name__ == '__main__':
    vk = V(token=BOT_TOKEN, group_id=config.bot_group_id, debug=True)
    vk.start_listen()
