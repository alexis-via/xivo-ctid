from xivo_cti.cti.cti_command import CTICommand
from xivo_cti.cti.cti_command_factory import CTICommandFactory
from xivo_cti.cti.commands.set_user_service import SetUserService
from xivo_cti.cti.commands.user_service.set_forward import SetForward


class EnableNoAnswerForward(SetForward):

    FUNCTION_NAME = 'fwd'
    ENABLE_NAME = 'enablerna'
    DESTINATION_NAME = 'destrna'

    required_fields = [CTICommand.CLASS, SetUserService.FUNCTION, SetUserService.VALUE]
    conditions = [(CTICommand.CLASS, SetUserService.COMMAND_CLASS),
                  (SetUserService.FUNCTION, FUNCTION_NAME),
                  ((SetUserService.VALUE, ENABLE_NAME), True)]
    _callbacks_with_params = []

CTICommandFactory.register_class(EnableNoAnswerForward)