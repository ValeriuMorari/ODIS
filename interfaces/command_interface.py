"""Socket command"""
from interfaces.custom_exceptions import CommandTemplateError, InvalidInitialization, InvalidCommand
import re

METHOD_PATTERN = r'^.*(?=\()'
ARGS_PATTERN = r'(?<=\().*(?=\))'


class CommandInterface:
    """
    Command Generic class
    """

    def __init__(self, component_class) -> None:
        self.obj = None
        self.component_class = component_class

    def initialize_object(self, message) -> str:
        """
        method responsible to register automated tool object
        :param message: Raw socket message
        :return: None
        """
        command = Command(message)
        method, args = command.dispatch()
        if "initialize" not in method:
            raise InvalidInitialization
        self.obj = self.component_class.initialize(*args)
        return "initialized"

    def execute_command(self, message: str):
        """

        :param message:
        :return:
        """
        command = Command(message)
        return command.execute(self.obj)


class Command:

    def __init__(self, command: str):
        """
        :param command: string command according to template:
        command(arg1; arg2; ...; argN)
        """
        self.command = command

    def dispatch(self) -> (str, tuple):
        """
        Dispatch command to method string and tuple of arguments
        :return: method string, tuple of arguments
        """
        args = re.search(ARGS_PATTERN, self.command)
        method = re.search(METHOD_PATTERN, self.command)
        if method is None:
            raise CommandTemplateError
        if args and args.group():
            args = args.group().split(";")
        else:
            args = []
        method = method.group()
        return method, args

    def execute(self, component: object):
        """
        Executes command in accordance to mentioned message & automation component
        :param component: automation component object
        :return: result in string format
        """
        method, args = self.dispatch()
        if not hasattr(component, method):
            raise InvalidCommand
        call = component.__getattribute__(method)
        response = call(*args)
        return str(response)
