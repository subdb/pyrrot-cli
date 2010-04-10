'''
Created on 02/04/2010

@author: Jr. Hames


Usage : python Pyrrot2Service.py install
Usage : python Pyrrot2Service.py start
Usage : python Pyrrot2Service.py stop
Usage : python Pyrrot2Service.py remove

C:\>python Pyrrot2Service.py  --username <username> --password <PASSWORD> --startup auto install

'''

import Pyrrot2
import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil

class Pyrrot2Service(win32serviceutil.ServiceFramework):
    _svc_name_ = "Pyrrot"
    _svc_display_name_ = "Pyrrot2"
    _svc_description_ = "A multiplatform (should work on Windows, Linux and Mac) client written in Python for SubDB."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        import servicemanager
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))

        self.timeout = 10000
        self.can_run = True
        self.retries = 0
        
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                Pyrrot2.save()
                servicemanager.LogInfoMsg("Pyrrot2 - STOPPED")
                break
            else:
                self.retries += 1
                if self.can_run:
                    for folder in Pyrrot2.DIRECTORIES:
                        Pyrrot2.download_subtitles(folder, Pyrrot2.LANGUAGES)
                        Pyrrot2.upload_subtitles(folder)
                        self.can_run = False
                elif self.retries == 180:
                    self.can_run = True
                    self.retries = 0


def ctrlHandler(ctrlType):
   return True

if __name__ == '__main__':
   win32api.SetConsoleCtrlHandler(ctrlHandler, True)
   win32serviceutil.HandleCommandLine(Pyrrot2Service)
