from collections import OrderedDict
from freenas.client.protocol import DDPProtocol
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource

import imp
import inspect
import json
import os
import subprocess
import sys


class Application(WebSocketApplication):

    protocol_class = DDPProtocol

    def __init__(self, *args, **kwargs):
        self.middleware = kwargs.pop('middleware')
        super(Application, self).__init__(*args, **kwargs)
        self.authenticated = self._check_permission()

    def _send(self, data):
        self.ws.send(json.dumps(data))

    def send_error(self, message, error, stacktrace=None):
        self._send({
            'msg': 'result',
            'id': message['id'],
            'error': {
                'error': error,
                'stacktrace': stacktrace,
            },
        })

    def _check_permission(self):
        remote = '{0}:{1}'.format(
            self.ws.environ['REMOTE_ADDR'], self.ws.environ['REMOTE_PORT']
        )

        proc = subprocess.Popen([
            '/usr/bin/sockstat', '-46c', '-p', self.ws.environ['REMOTE_PORT']
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in proc.communicate()[0].strip().splitlines()[1:]:
            cols = line.split()
            if cols[-1] == remote and cols[0] == 'root':
                return True
        return False

    def call_method(self, message):

        try:
            self._send({
                'id': message['id'],
                'msg': 'result',
                'result': self.middleware.call_method(
                    message['method'], message.get('params') or []
                ),
            })
        except Exception as e:
            self.send_error(message, str(e))

    def on_open(self):
        pass

    def on_close(self, *args, **kwargs):
        pass

    def on_message(self, message):

        if not self.authenticated:
            self.send_error(message, 'Not authenticated')
            return

        if message['msg'] == 'method':
            self.call_method(message)


class MResource(Resource):

    def __init__(self, *args, **kwargs):
        self.middleware = kwargs.pop('middleware')
        super(MResource, self).__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        """
        Method entirely copied except current_app call to include middleware
        """
        environ = environ
        is_websocket_call = 'wsgi.websocket' in environ
        current_app = self._app_by_path(environ['PATH_INFO'], is_websocket_call)

        if current_app is None:
            raise Exception("No apps defined")

        if is_websocket_call:
            ws = environ['wsgi.websocket']
            current_app = current_app(ws, middleware=self.middleware)
            current_app.ws = ws  # TODO: needed?
            current_app.handle()
            # Always return something, calling WSGI middleware may rely on it
            return []
        else:
            return current_app(environ, start_response)


class Middleware(object):

    def __init__(self):
        self._services = {}
        self._plugins_load()

    def _plugins_load(self):
        from middlewared.service import Service
        plugins_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'plugins',
        )
        if not os.path.exists(plugins_dir):
            return

        for f in os.listdir(plugins_dir):
            if not f.endswith('.py'):
                continue
            f = f[:-3]
            fp, pathname, description = imp.find_module(f, [plugins_dir])
            try:
                mod = imp.load_module(f, fp, pathname, description)
            finally:
                if fp:
                    fp.close()

            for attr in dir(mod):
                attr = getattr(mod, attr)
                if not inspect.isclass(attr):
                    continue
                if attr is Service:
                    continue
                if issubclass(attr, Service):
                    self.register_service(attr(self))

    def register_service(self, service):
        self._services[service._meta.namespace] = service

    def call_method(self, method, params):
        service, method = method.rsplit('.', 1)
        return getattr(self._services[service], method)(*params)

    def run(self):
        server = WebSocketServer(('', 8000), MResource(OrderedDict([
            ('/websocket', Application),
        ]), middleware=self))
        server.serve_forever()


if __name__ == '__main__':
    modpath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
    )
    if modpath not in sys.path:
        sys.path.insert(0, modpath)
    Middleware().run()