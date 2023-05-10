from _pytest.fixtures import fixture

from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations, Conversations, Actions


@fixture()
def actions_and_conversations() -> ActionsAndConversations:
    return ActionsAndConversations()


@fixture()
def conversations(actions_and_conversations) -> Conversations:
    return actions_and_conversations.conversations


@fixture()
def actions(actions_and_conversations) -> Actions:
    return actions_and_conversations.actions
