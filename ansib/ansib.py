import shutil
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
import ansible.constants as C
import yaml
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def __init__(self, *args, hosts_file="../hosts"):
        CallbackBase.__init__(self, *args)
        self.result_for_flask = dict()

    def v2_runner_on_ok(self, result, **kwargs):
        """
        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        if host.name not in self.result_for_flask:
            self.result_for_flask[host.name] = list()
        self.result_for_flask[host.name].append(result._result)
        # print(self.result_for_flask)

    v2_runner_on_failed = v2_runner_on_ok
    v2_runner_on_unreachable = v2_runner_on_ok
    v2_runner_on_skipped = v2_runner_on_ok

    def get_list_of_hosts(self, hosts_file="../hosts"):
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=hosts_file)
        return inventory.get_hosts()

    def use_pb(self, playbook_yaml_file, hosts_file="../hosts", single_host=None):
        # since API is constructed for CLI it expects certain options to always be set,
        # named tuple 'fakes' the args parsing options object
        Options = namedtuple('Options', ['connection', 'module_path', 'forks',
                                         'become', 'become_method', 'become_user', 'check', 'diff'])
        options = Options(connection='ssh', module_path='%s/' % (ROOT_DIR), forks=10,
                          become=None, become_method=None, become_user=None, check=False, diff=False)

        # initialize needed objects
        # Takes care of finding and reading yaml, json and ini files
        loader = DataLoader()
        passwords = dict(vault_pass='secret')
        # create inventory, use path to host config file as source or hosts in a comma separated string
        inventory = InventoryManager(loader=loader, sources=hosts_file)

        # variable manager takes care of merging all the different sources
        # to give you a unifed view of variables available in each context
        if single_host:
            list_of_hosts = inventory.get_hosts(pattern=single_host)
            inventory.restrict_to_hosts(list_of_hosts)

        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # create datastructure that represents our play, including tasks,
        # this is basically what our YAML loader does internally.
        with open(playbook_yaml_file, 'r') as stream:
            play_source = yaml.safe_load(stream)[0]

        # Create play object, playbook objects use .load instead of init or new methods,
        # this will also automatically create the task objects from the info provided in play_source
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        # Run it - instantiate task queue manager, which takes care of forking and setting up all objects
        # to iterate over host list and tasks
        tqm = None
        try:
            tqm = TaskQueueManager(inventory=inventory, variable_manager=variable_manager,
                                   loader=loader, options=options, passwords=passwords,
                                   # Use our custom callback
                                   stdout_callback=self
                                   )
            # most interesting data for a play is actually sent to the callback's methods
            result = tqm.run(play)
        finally:
            # we always need to cleanup child procs and the structres we use to communicate with them
            if tqm is not None:
                tqm.cleanup()

            # Remove ansible tmpdir
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
