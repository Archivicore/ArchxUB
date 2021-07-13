# pylint: disable=missing-module-docstring

class StopConversation(Exception):
    """ raise if conversation has terminated """


class ProcessCanceled(Exception):
    """ raise if thread has terminated """


class ArchxBotNotFound(Exception):
    """ raise if Archx bot not found """
