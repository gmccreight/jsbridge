# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
# 
# The Original Code is Mozilla Corporation Code.
# 
# The Initial Developer of the Original Code is
# Mikeal Rogers.
# Portions created by the Initial Developer are Copyright (C) 2008 -2009
# the Initial Developer. All Rights Reserved.
# 
# Contributor(s):
#  Mikeal Rogers <mikeal.rogers@gmail.com>
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

import socket
import os
import copy
from time import sleep

import mozrunner

import network
from jsobjects import JSObject

settings_env = 'JSBRIDGE_SETTINGS_FILE'

back_channel = None

parent = os.path.abspath(os.path.dirname(__file__))

window_string = "Components.classes['@mozilla.org/appshell/window-mediator;1'].getService(Components.interfaces.nsIWindowMediator).getMostRecentWindow('')"

class JSBridgeCLI(mozrunner.CLI):
    
    parser_options = copy.copy(mozrunner.CLI.parser_options)
    parser_options[('-D', '--debug',)] = dict(dest="debug", 
                                             action="store_true",
                                             help="Install debugging plugins.", 
                                             metavar="JSBRIDGE_DEBUG",
                                             default=False )
    parser_options[('-s', '--shell',)] = dict(dest="shell", 
                                             action="store_true",
                                             help="Start a Python shell",
                                             metavar="JSBRIDGE_SHELL",
                                             default=False )
    parser_options[('-u', '--usecode',)] = dict(dest="usecode", action="store_true",
                                               help="Use code module instead of iPython",
                                               default=False)
    parser_options[('-P', '--port')] = dict(dest="port", default="24242",
                                            help="TCP port to run jsbridge on.")
    
    debug_plugins = [os.path.join(parent, 'xpi', 'xush-0.2-fx.xpi')]
    
    def get_profile(self, *args, **kwargs):
        if self.options.debug:
            kwargs.setdefault('preferences', 
                              {}).update({'extensions.checkCompatibility':False})
        profile = super(JSBridgeCLI, self).get_profile(*args, **kwargs)
        profile.install_plugin(os.path.join(parent, 'extension'))
        if self.options.debug:
            for p in self.debug_plugins:
                profile.install_plugin(p)
        return profile
        
    def get_runner(self, *args, **kwargs):
        runner = super(JSBridgeCLI, self).get_runner(*args, **kwargs)
        if self.options.debug:
            runner.cmdargs.append('-jsconsole')
        return runner
        
    def run(self):
        runner = self.parse_and_get_runner()
        runner.start()
        self.start_jsbridge_network()
        if self.options.shell:
            self.start_shell(runner)
        else:
            try:
                runner.wait()
            except KeyboardInterrupt:
                runner.stop()
    
    def start_shell(self, runner):
        try:
            import IPython
        except:
            IPython = None
        bridge = JSObject(self.bridge, window_string)
        
        if IPython is None or self.options.usecode:
            import code
            code.interact(local={"bridge":bridge, 
                                 "getBrowserWindow":lambda : getBrowserWindow(self.bridge),
                                 "back_channel":self.back_channel,
                                 })
        else:
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed([])
            ipshell(local_ns={"bridge":bridge, 
                              "getBrowserWindow":lambda : getBrowserWindow(self.bridge),
                              "back_channel":self.back_channel,
                              })
        runner.stop()
        
    def start_jsbridge_network(self, timeout=10):
        port = int(self.options.port)
        host = '127.0.0.1'
        ttl = 0
        while ttl < timeout:
            sleep(.25)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.close()
                break
            except socket.error:
                pass
        self.back_channel, self.bridge = network.create_network(host, port)

def cli():
    JSBridgeCLI().run()


def getBrowserWindow(bridge):
    return JSObject(bridge, "Components.classes['@mozilla.org/appshell/window-mediator;1'].getService(Components.interfaces.nsIWindowMediator).getMostRecentWindow('')")
    
def getPreferencesWindow(bridge):
    bridge = JSObject(bridge, "openPreferences()")
    sleep(1)
    return bridge






